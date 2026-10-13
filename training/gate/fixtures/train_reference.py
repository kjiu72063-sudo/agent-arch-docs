from transformers import AutoModelForCausalLM, AutoTokenizer, DefaultDataCollator,Trainer,TrainingArguments,PreTrainedModel,PretrainedConfig,DataCollatorForTokenClassification, AutoConfig,PretrainedConfig
from peft import LoraConfig, get_peft_model, TaskType,PeftModel
import torch
from torch import nn
from torch.nn import functional as F
import math
from typing import List, Optional, Tuple, Union
import torch.utils.checkpoint
import os
import pandas as pd
from torch.utils.data import IterableDataset, Dataset
import json
import numpy as np
from transformers.modeling_outputs import CausalLMOutputWithPast

#计算KL散度损失
def compute_kl_div_loss(
        logits, #经过temperature软化后的学生logits
        teacher_logits, #经过temperature软化后的教师logits
        target,
        padding_id,
        reduction="sum",
):
    log_probs = torch.log_softmax(logits, -1, dtype=torch.float32)
    teacher_probs = torch.softmax(teacher_logits, -1, dtype=torch.float32)
    teacher_log_probs = torch.log_softmax(teacher_logits, -1, dtype=torch.float32)
    kl = (teacher_probs * (teacher_log_probs - log_probs))
    kl = kl.sum(-1)
    if reduction == "sum":
        pad_mask = target.eq(padding_id)
        kl = kl.masked_fill_(pad_mask, 0.0)
        kl = kl.sum()
    return kl

class MyDataset(Dataset):
    def __init__(self, data_path, tokenizer, max_seq_len):
        super().__init__()
        self.data_path = data_path
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        self.padding_id = tokenizer.pad_token_id
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    def __len__(self):
        return len(self.data)
    def __getitem__(self, index):
        data_line = self.data[index]
        instruction_text = data_line['instruction']
        input_text = data_line['input']
        output_text = data_line['output']
        query = instruction_text + input_text
        answer = output_text + self.tokenizer.eos_token
        messages = []
        messages.append({'role': 'user', 'content': query})
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False)
        prompt_input_ids = self.tokenizer.encode(prompt)
        answer_input_ids = self.tokenizer.encode(answer)
        # 通过mask language model的方式进行训练
        input_ids = prompt_input_ids + answer_input_ids
        labels = [-100] * len(prompt_input_ids) + answer_input_ids
        attention_mask = [1] * len(input_ids)
        text_len = len(input_ids)
        if text_len > self.max_seq_len:
            input_ids = input_ids[:self.max_seq_len]
            labels = labels[:self.max_seq_len]
            attention_mask = attention_mask[:self.max_seq_len]
        else:
            input_ids = input_ids + [self.tokenizer.pad_token_id] * (self.max_seq_len - text_len)
            labels = labels + [-100] * (self.max_seq_len - text_len)
            attention_mask = attention_mask + [0] * (self.max_seq_len - text_len)
        return {'input_ids': torch.tensor(input_ids), 'attention_mask': torch.tensor(attention_mask),
                'labels': torch.tensor(labels)}

#定义peft训练的trainer
class Custom_Trainer(Trainer):
    def __init__(
            self,
            model=None,
            teacher_model=None,
            args=None,
            data_collator=None,
            train_dataset=None,
            eval_dataset=None,
            tokenizer=None,
            model_init=None,
            compute_metrics=None,
            callbacks=None,
            preprocess_logits_for_metrics=None,
            temperature=None, #白盒蒸馏的温度系数
    ):
        super().__init__(
            model,
            args,
            data_collator,
            train_dataset,
            eval_dataset,
            tokenizer,
            model_init,
            compute_metrics,
            callbacks,
            preprocess_logits_for_metrics,
        )
        self.teacher_model = teacher_model
        self.temperature= temperature
    #损失计算函数
    def compute_loss(self, model, inputs, return_outputs=False,num_items_in_batch=None):
        outputs = model(**inputs) #学生输出
        with torch.no_grad():
            teacher_outputs = self.teacher_model(**inputs)
        loss = outputs.loss #学生损失
        logits = outputs.logits #学生logtits
        teacher_logits = teacher_outputs.logits
        # 如果教师模型和学生模型异构，会导致输出特征图大小不匹配，对学生模型进行padding或对教师模型进行截断
        if logits.shape[-1] != teacher_logits.shape[-1]:
            dimension_diff = teacher_logits.shape[-1] - logits.shape[-1]
            if dimension_diff > 0:
                pad_logits = torch.zeros((logits.shape[0], logits.shape[1], dimension_diff)).to(logits.device)
                logits = torch.cat([logits, pad_logits], dim=-1)
            teacher_logits = teacher_logits[:, :, :logits.shape[-1]]
        labels = inputs['labels']
        kl = compute_kl_div_loss(logits/self.temperature, teacher_logits/self.temperature, labels, padding_id=-100)
        alpha=0.5 #损失比例系数
        loss_total=alpha * kl + (1-alpha) * loss
        return loss_total
    

if __name__ == '__main__':
    # 学生模型
    model = AutoModelForCausalLM.from_pretrained("/root/.cache/modelscope/hub/models/Qwen/Qwen3-1.7B")
    lora_config = LoraConfig(
        r=8,
        lora_alpha=256, #更偏向于lora adapter部分
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.1,
        task_type=TaskType.CAUSAL_LM)
    # 使用lora方法训练
    model = get_peft_model(model, lora_config)
    model.cuda()
    #print("model:",model)
    print("model_parameters:",model.print_trainable_parameters())
    tokenizer = AutoTokenizer.from_pretrained("/root/.cache/modelscope/hub/models/Qwen/Qwen3-1.7B")
    # 教师模型，在给定数据上通过lora微调
    teacher_model = AutoModelForCausalLM.from_pretrained("/root/.cache/modelscope/hub/models/Qwen/Qwen3-4B-Instruct-2507")
    # 是否加载lora模型
    lora_path = '/root/autodl-tmp/LLaMA-Factory/saves/qwen3-4b/lora/sft'
    teacher_model = PeftModel.from_pretrained(teacher_model, lora_path).cuda()
    #老师模型设置为推理模式，不进行参数更新
    teacher_model.eval()
    args = TrainingArguments(output_dir='./results1', #results
                             num_train_epochs=10,
                             do_train=True,
                             per_device_train_batch_size=1,
                             gradient_accumulation_steps=16,
                             logging_steps=10,
                             report_to='tensorboard',
                             save_strategy='steps', #'epoch',
                             save_steps=500,
                             save_total_limit=10,
                             bf16=True,
                             learning_rate=0.0005,
                             lr_scheduler_type='cosine',
                             dataloader_num_workers=4,
                             dataloader_pin_memory=True,
                             ) 
    dataset = MyDataset('identity_modify.json', tokenizer=tokenizer, max_seq_len=512)
    print("dataset:",dataset)
    trainer = Custom_Trainer(model=model,
                        teacher_model=teacher_model,
                        args=args,
                        train_dataset=dataset,
                        tokenizer=tokenizer,
                        data_collator=DefaultDataCollator(),
                        temperature=6) #指定温度系数超参数，一般取值范围:【3-20】
    # 如果是初次训练resume_from_checkpoint为false，接着checkpoint继续训练，为True
    trainer.train(resume_from_checkpoint=False)
    trainer.save_model('./saves1') #saves1
    trainer.save_state()



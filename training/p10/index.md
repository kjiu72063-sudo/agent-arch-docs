---
title: Part 10 · 练习案例库
---

# Part 10 · 练习案例库

::: info 这是答案册，不是教程
Part 1–6 与 Part 9 每个 Part 末尾都留了 **2 道动手题**，一共 **14 道**。题目写在各 Part 末页，**完整答案（步骤 + 命令 + 截图）集中在本 Part**。

用法只有一句话：**先自己做，卡在哪一步再看那一步**。这本册子不是用来从头读到尾的。

**所有案例默认在 AutoDL 云上做**（本地没有 N 卡是常态）—— 见下面「三个约定」。
:::

## 怎么用这本案例册

| 你的身份 | 用法 |
|---|---|
| **自学** | 读完一个 Part → 去该 Part 末页做那 2 道题 → 自己跑完，再翻答案逐步对 |
| **复盘** | 只读「⑤ 预期结果」和「⑥ 常见报错」两节，检查自己当时的判读对不对 |
| **教学** | 题目可直接当作业布置；「④ 分步操作」里的截图槽就是演示截图该放的位置 |

> 每道题都是「**能出判定标准**」的：不是"跑起来不报错就算过"，而是"看到这个输出才算过"。

## 14 道案例总览

按 **Part 分 7 组**，每组一道**基础题** + 一道**综合题**。基础题练单点技能闭环，综合题要跨小节、必须产出对比结论。

::: tip 卡片上的徽章
- **基础 / 综合** —— 难度。
- **单卡** —— 该案例**只租 1 张卡**即可完成（多卡部分通过配置 + 账本推演练习）。
  这类案例页首会给出**预估费用与省钱姿势**。没这个徽章的案例默认按 1–2 张卡准备。
- **免卡** —— 该案例**完全不需要 GPU**（纯计算 / 纯数据处理），在本地或云主机**无卡模式**下即可完成，页首标 **¥0**。
:::

<div style="display:grid;grid-template-columns:1fr;gap:14px;margin:20px 0;">

  <div style="border:1px solid var(--vp-c-divider);border-radius:12px;padding:15px 17px;background:var(--vp-c-bg-soft);">
    <div style="display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;margin-bottom:12px;">
      <span style="font-weight:700;font-size:15px;letter-spacing:.02em;color:var(--vp-c-text-1);">PART 1</span>
      <span style="font-size:12px;color:var(--vp-c-text-3);letter-spacing:.06em;text-transform:uppercase;">基础与环境</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr;gap:10px;">
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #d97757;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#d97757;letter-spacing:.04em;">C01</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">基础</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">在 AutoDL 上从零搭好 LLaMA-Factory 环境</div>
        <a href="/training/p10/c01-llamafactory-env" style="font-size:13px;font-weight:600;color:#d97757;text-decoration:none;">查看答案 →</a>
      </div>
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #c2410c;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#c2410c;letter-spacing:.04em;">C02</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">综合</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">下载 Qwen3-4B-Base 并跑通 WebUI 对话</div>
        <a href="/training/p10/c02-model-download-webui" style="font-size:13px;font-weight:600;color:#c2410c;text-decoration:none;">查看答案 →</a>
      </div>
    </div>
  </div>

  <div style="border:1px solid var(--vp-c-divider);border-radius:12px;padding:15px 17px;background:var(--vp-c-bg-soft);">
    <div style="display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;margin-bottom:12px;">
      <span style="font-weight:700;font-size:15px;letter-spacing:.02em;color:var(--vp-c-text-1);">PART 2</span>
      <span style="font-size:12px;color:var(--vp-c-text-3);letter-spacing:.06em;text-transform:uppercase;">数据工程</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr;gap:10px;">
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #d97757;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#d97757;letter-spacing:.04em;">C03</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">基础</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">单卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">制作一份合规的 Alpaca 格式自定义数据集</div>
        <a href="/training/p10/c03-alpaca-dataset" style="font-size:13px;font-weight:600;color:#d97757;text-decoration:none;">查看答案 →</a>
      </div>
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #c2410c;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#c2410c;letter-spacing:.04em;">C04</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">综合</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">单卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">多轮对话 → ShareGPT 格式 → 接入 LLaMA-Factory</div>
        <a href="/training/p10/c04-sharegpt-dataset" style="font-size:13px;font-weight:600;color:#c2410c;text-decoration:none;">查看答案 →</a>
      </div>
    </div>
  </div>

  <div style="border:1px solid var(--vp-c-divider);border-radius:12px;padding:15px 17px;background:var(--vp-c-bg-soft);">
    <div style="display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;margin-bottom:12px;">
      <span style="font-weight:700;font-size:15px;letter-spacing:.02em;color:var(--vp-c-text-1);">PART 3</span>
      <span style="font-size:12px;color:var(--vp-c-text-3);letter-spacing:.06em;text-transform:uppercase;">方法与加速</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr;gap:10px;">
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #d97757;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#d97757;letter-spacing:.04em;">C05</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">基础</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">单卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">用 LoRA 对 Qwen3-4B-Base 做一次完整 SFT</div>
        <a href="/training/p10/c05-lora-sft" style="font-size:13px;font-weight:600;color:#d97757;text-decoration:none;">查看答案 →</a>
      </div>
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #c2410c;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#c2410c;letter-spacing:.04em;">C06</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">综合</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">单卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">QLoRA(4-bit) vs LoRA：显存与效果对照</div>
        <a href="/training/p10/c06-qlora-vs-lora" style="font-size:13px;font-weight:600;color:#c2410c;text-decoration:none;">查看答案 →</a>
      </div>
    </div>
  </div>

  <div style="border:1px solid var(--vp-c-divider);border-radius:12px;padding:15px 17px;background:var(--vp-c-bg-soft);">
    <div style="display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;margin-bottom:12px;">
      <span style="font-weight:700;font-size:15px;letter-spacing:.02em;color:var(--vp-c-text-1);">PART 4</span>
      <span style="font-size:12px;color:var(--vp-c-text-3);letter-spacing:.06em;text-transform:uppercase;">分布式训练</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr;gap:10px;">
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #d97757;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#d97757;letter-spacing:.04em;">C07</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">基础</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">单卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">单卡实测 + 多卡推演：DDP 与 ZeRO-2 的每卡显存账</div>
        <a href="/training/p10/c07-ddp-zero2" style="font-size:13px;font-weight:600;color:#d97757;text-decoration:none;">查看答案 →</a>
      </div>
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #c2410c;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#c2410c;letter-spacing:.04em;">C08</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">综合</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">单卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">单卡 offload 真跑 + FSDP 配置对照</div>
        <a href="/training/p10/c08-zero3-fsdp" style="font-size:13px;font-weight:600;color:#c2410c;text-decoration:none;">查看答案 →</a>
      </div>
    </div>
  </div>

  <div style="border:1px solid var(--vp-c-divider);border-radius:12px;padding:15px 17px;background:var(--vp-c-bg-soft);">
    <div style="display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;margin-bottom:12px;">
      <span style="font-weight:700;font-size:15px;letter-spacing:.02em;color:var(--vp-c-text-1);">PART 5</span>
      <span style="font-size:12px;color:var(--vp-c-text-3);letter-spacing:.06em;text-transform:uppercase;">知识蒸馏</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr;gap:10px;">
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #d97757;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#d97757;letter-spacing:.04em;">C09</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">基础</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">单卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">跑通白盒蒸馏：教师 4B → 学生 1.7B</div>
        <a href="/training/p10/c09-whitebox-distill" style="font-size:13px;font-weight:600;color:#d97757;text-decoration:none;">查看答案 →</a>
      </div>
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #c2410c;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#c2410c;letter-spacing:.04em;">C10</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">综合</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">单卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">蒸馏 vs 小模型直接 SFT 的效果对比</div>
        <a href="/training/p10/c10-distill-vs-sft" style="font-size:13px;font-weight:600;color:#c2410c;text-decoration:none;">查看答案 →</a>
      </div>
    </div>
  </div>

  <div style="border:1px solid var(--vp-c-divider);border-radius:12px;padding:15px 17px;background:var(--vp-c-bg-soft);">
    <div style="display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;margin-bottom:12px;">
      <span style="font-weight:700;font-size:15px;letter-spacing:.02em;color:var(--vp-c-text-1);">PART 6</span>
      <span style="font-size:12px;color:var(--vp-c-text-3);letter-spacing:.06em;text-transform:uppercase;">部署与推理</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr;gap:10px;">
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #d97757;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#d97757;letter-spacing:.04em;">C11</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">基础</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">单卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">vLLM + FastAPI 部署微调后模型并调通</div>
        <a href="/training/p10/c11-vllm-fastapi" style="font-size:13px;font-weight:600;color:#d97757;text-decoration:none;">查看答案 →</a>
      </div>
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #c2410c;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#c2410c;letter-spacing:.04em;">C12</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">综合</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">单卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">Ollama 自定义模型 + 前缀缓存/批处理吞吐优化</div>
        <a href="/training/p10/c12-ollama" style="font-size:13px;font-weight:600;color:#c2410c;text-decoration:none;">查看答案 →</a>
      </div>
    </div>
  </div>

  <div style="border:1px solid var(--vp-c-divider);border-radius:12px;padding:15px 17px;background:var(--vp-c-bg-soft);">
    <div style="display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;margin-bottom:12px;">
      <span style="font-weight:700;font-size:15px;letter-spacing:.02em;color:var(--vp-c-text-1);">PART 9</span>
      <span style="font-size:12px;color:var(--vp-c-text-3);letter-spacing:.06em;text-transform:uppercase;">显存与容量规划</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr;gap:10px;">
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #d97757;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#d97757;letter-spacing:.04em;">C13</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">基础</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">免卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">用 9-15 计算器做一次容量规划</div>
        <a href="/training/p10/c13-calculator-planning" style="font-size:13px;font-weight:600;color:#d97757;text-decoration:none;">查看答案 →</a>
      </div>
      <div style="border:1px solid var(--vp-c-divider);border-left:3px solid #c2410c;border-radius:8px;padding:12px 14px;background:var(--vp-c-bg);">
        <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;font-weight:700;color:#c2410c;letter-spacing:.04em;">C14</span>
          <span style="font-size:10px;font-weight:600;color:var(--vp-c-text-2);background:var(--vp-c-default-soft);border-radius:99px;padding:1px 8px;">综合</span>
          <span style="font-size:10px;font-weight:600;color:#b45309;background:var(--vp-c-warning-soft);border-radius:99px;padding:1px 8px;">免卡</span>
        </div>
        <div style="font-weight:600;font-size:14px;line-height:1.5;color:var(--vp-c-text-1);margin-bottom:9px;">手算复现计算器读数（偏差 ≤ 5%）</div>
        <a href="/training/p10/c14-handcalc-reproduce" style="font-size:13px;font-weight:600;color:#c2410c;text-decoration:none;">查看答案 →</a>
      </div>
    </div>
  </div>

</div>

::: details 为什么 Part 7 / Part 8 不配题
Part 7（综合实战）与 Part 8（附录）本身已是综合/查阅性质——前者就是一道大综合题，后者是速查卡而非练习对象，再配小题只会重复。
:::

## 案例页的七段结构

每道案例都是一页，固定七段——**你在每页都会看到同样的结构，位置可以直接记**：

| 段 | 作用 | 阅读时机 |
|---|---|---|
| ① 题目 | 复述题干 + 一句话目标 | 做之前 |
| ② 你会练到什么 | 3–5 条技能点，各自对应哪个小节 | 做之前（确认自己是不是已经会了） |
| ③ 前置条件 | 硬件 / 软件 / 数据 / 依赖，逐条可核对 | 做之前 |
| ④ **分步操作** | 步骤 + 命令 + **每一步的选项说明** + **截图槽** ← 本册的核心 | 卡住时对照 |
| ⑤ 预期结果 | 每步该看到什么 + **判定标准** | 做的时候逐项打勾 |
| ⑥ 常见报错 | 真实报错 → 原因 → 处置 | 报错时直接查 |
| ⑦ 延伸 | 改一个变量会怎样 | 做完之后 |

### ④ 分步操作里的「选项说明」是什么

案例里每一步除命令外，都附一张**选项决策表**，回答三件事：

| 列 | 回答什么 | 例子（C02 步骤 2） |
|---|---|---|
| **选项 / 判断** | 这一步有哪些可选做法 | 魔搭 vs HuggingFace；命令行下载 vs `git clone` |
| **含义** | 这个选项具体是什么 | 两个托管站同一个模型，权重完全相同 |
| **为什么这么选** | 本案例选它、以及**其他选项意味着什么** | 国内访问魔搭不用科学上网，HF 要代理且限速 |

更复杂的选择（如 WebUI 的量化和加速下拉框）会**按每个选项单独列出"选了会怎样"**——因为那些下拉框选错的后果各不相同：量化选错是跑不动，模板选错是答非所问，加速选错是直接报错。

> **为什么值得这么细**：讲义正文讲的是"有哪些选项"，案例补的是"**在你的场景下选哪个、为什么**"。看懂选项和敢做选择，是两回事。

## 截图槽是什么

案例里的操作截图**需要你自己跑一遍才能截**，所以页面里先放的是**槽位**，而不是图：

```text
> 🖼 截图槽 c01-03 — 应截：终端执行 conda create ... 后的完整输出
> 文件名：c01/03-conda-create.png
```

- **放图路径**：`agent-arch-docs/.vitepress/public/training/cases/cNN/JJ-slug.png`
- **命名规则**：`cNN` = 案例号（`c01`）；`JJ` = 两位步骤号（`03`）；`slug` = 短英文描述
- **为什么先放槽、不直接写 `![]()`**：图没到位时写图片引用会让 `npm run build` 因死链直接失败。图放好后再把槽换成 `![说明](/training/cases/cNN/JJ-slug.png)` 即可。

## 三个约定

### 1. 默认在云上做（AutoDL），不是本地

::: warning 先说清楚：本册所有案例默认跑在 AutoDL 上
**绝大多数人本地没有 NVIDIA 卡，也搭不了。** 所以案例的前置条件、命令、磁盘路径、显存口径，**全部按云端来写**；只有明确标了「本地差异」的地方才需要在 Windows 上做不同处理。

- 云端为什么是主路径、怎么选卡、怎么连、怎么省钱 → [**1-11 AutoDL 租卡：云上环境搭建全流程**](/training/p1/11-autodl)
- 本册案例的**第 1 步几乎都是"创建 / 开机 AutoDL 实例"**，这不是可跳过的准备动作，是题目的一部分。
:::

云端环境下有 **3 个必须记住的固定点**，后面每道题都会用到：

| 固定点 | 内容 | 踩错会怎样 |
|---|---|---|
| **开区** | 选自己网络最快的地区（如西北 B 区） | 镜像下载慢、SSH 卡 |
| **数据盘** | 大文件一律放 `/root/autodl-tmp`（约 50 GB）；系统盘 `/root` 只有 ~30 GB 且可能重置 | 下两个模型就 `No space left on device`，重开机还可能丢文件 |
| **关机** | 用完回控制台**关机**；SSH 里敲 `exit` 不算 | 实例一直计费，睡一觉起来余额没了 |

### 2. 命令与环境

案例命令以 Ubuntu / AutoDL 为主，Windows 本地差异会单独标注。所有命令都来自讲义对应页，不额外引入新依赖。

### 3. 显存读数

所有显存数字以 `nvidia-smi` 的 **MiB 读数 ÷ 1024** 为准（即 GiB）。GB/GiB 的换算是 Part 9 的考点，案例里会明确区分。

::: tip 配套阅读
案例只讲"怎么选"，**选项本身的完整清单**在讲义正文里：
- **云上搭环境的完整流程** → [1-11 AutoDL 租卡](/training/p1/11-autodl)（先看这页，再回来看案例）
- 本地 / 云端两条路怎么选 → [1-5 本地与云端环境](/training/p1/05-env)
- 量化类型（bnb / HQQ / EETQ）→ [1-9 调参难点（上）](/training/p1/09-tuning-quant)
- 调度器 / RoPE 插值 / 加速方案 → [1-10 调参难点（下）· 每个选项是什么意思](/training/p1/10-tuning-rope#每个选项是什么意思)
- 模型与落盘路径 → [1-8 模型下载与 WebUI](/training/p1/08-webui)
:::

---

> 回到各 Part 末页做题目，或直接开始：[C01 在 AutoDL 上搭好 LLaMA-Factory 环境](/training/p10/c01-llamafactory-env)

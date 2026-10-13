import DefaultTheme from 'vitepress/theme'
import './style.css'
import P9Calculator from '../components/P9Calculator.vue'

// 自定义主题：继承默认布局，叠加设计 token（见 style.css）
export default {
  ...DefaultTheme,
  enhanceApp({ app }) {
    // Part 9「显存与容量规划」交互式计算器（9-15 内嵌使用）
    app.component('P9Calculator', P9Calculator)
  },
}

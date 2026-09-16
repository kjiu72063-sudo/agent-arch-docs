import DefaultTheme from 'vitepress/theme'
import './style.css'

// 自定义主题：继承默认布局，叠加设计 token（见 style.css）
// 后续可在此注册 ECharts 关系图/对比矩阵组件：
// import RelationChart from '../components/RelationChart.vue'
// export default { ...DefaultTheme, enhanceApp: ({ app }) => app.component('RelationChart', RelationChart) }

export default DefaultTheme

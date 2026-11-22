/**
 * 导航框配置
 *
 * 只给「同辈并列」关系明确的大势力配置。页面通过 frontmatter 的 navbox 字段挂载：
 *   navbox: [ipc, stonehearts]
 *
 * items 里的名称如果站内已有条目，会自动变成链接；没有则渲染为灰色待补项。
 */
export interface NavBoxGroup {
  label: string
  items: string[]
}

export interface NavBox {
  title: string
  groups: NavBoxGroup[]
  note?: string
}

const navboxes: Record<string, NavBox> = {
  ipc: {
    title: '星际和平公司',
    groups: [
      {
        label: '七部门',
        items: [
          '战略投资部',
          '市场开拓部',
          '业务巩固部',
          '技术研发部',
          '人才激励部',
          '传统项目部',
          '筑材物流部'
        ]
      },
      {
        label: '石心十人',
        items: ['钻石', '砂金', '托帕', '翡翠', '真珠']
      }
    ],
    note: '石心十人其余成员官方尚未全部公开。'
  },
  stonehearts: {
    title: '石心十人',
    groups: [
      {
        label: '已知成员',
        items: ['钻石', '砂金', '托帕', '翡翠', '真珠']
      }
    ],
    note: '其余成员官方尚未全部公开。'
  }
}

export default navboxes

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
  },
  train: {
    title: '星穹列车',
    groups: [
      {
        label: '乘员',
        items: ['姬子', '瓦尔特', '丹恒', '三月七', '开拓者', '帕姆']
      }
    ],
    note: '帕姆是列车长，不参与战斗。'
  },
  hunters: {
    title: '星核猎手',
    groups: [
      {
        label: '已知成员',
        items: ['艾利欧', '卡芙卡', '刃', '银狼', '流萤']
      }
    ],
    note: '首领艾利欧从未正式登场。'
  },
  xianzhou: {
    title: '仙舟联盟',
    groups: [
      {
        label: '仙舟',
        items: ['罗浮', '朱明', '曜青', '方壶', '玉阙']
      },
      {
        label: '机构',
        items: ['云骑军', '十王司', '丹鼎司']
      }
    ],
    note: '其余仙舟与机构官方着墨较少。'
  }
}

export default navboxes

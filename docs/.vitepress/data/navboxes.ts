/**
 * 导航框配置
 *
 * 只给「同辈并列」关系明确的大势力配置。页面通过 frontmatter 的 navbox 字段挂载：
 *   navbox: [ipc, stonehearts]
 *
 * items 里的名称如果站内已有条目，会自动变成链接；没有则渲染为灰色待补项。
 */
export interface NavBoxGroup {
  // 字符串 = 词条名（自动查表）；对象 = 显式链接（用于尚未成条但有锚点的对象）
  items: (string | { text: string; link: string })[]
  label: string
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
          { text: '战略投资部', link: '/factions/ipc#七部门' },
          { text: '市场开拓部', link: '/factions/ipc#七部门' },
          { text: '业务巩固部', link: '/factions/ipc#七部门' },
          { text: '技术研发部', link: '/factions/ipc#七部门' },
          { text: '人才激励部', link: '/factions/ipc#七部门' },
          { text: '传统项目部', link: '/factions/ipc#七部门' },
          { text: '筑材物流部', link: '/factions/ipc#七部门' }
        ]
      },
      {
        label: '石心十人',
        items: ['钻石', '砂金', '托帕', '翡翠', '真珠', '舒俱', '欧泊', '龙晶']
      }
    ],
    note: '十人全名单与逐人档案见「石心十人」。'
  },
  stonehearts: {
    title: '石心十人',
    groups: [
      {
        label: '主管',
        items: ['钻石']
      },
      {
        label: '成员',
        items: [
          '托帕',
          '砂金',
          '翡翠',
          '真珠',
          '舒俱',
          '欧泊',
          '龙晶',
          { text: '苍刚', link: '/factions/stonehearts#逐人档案' },
          { text: '玛瑙', link: '/factions/stonehearts#逐人档案' },
          { text: '琥珀', link: '/factions/stonehearts#逐人档案' }
        ]
      }
    ],
    note: '十人名单出自千星纪游 PV「石心誓环·天平两端」。苍刚、玛瑙、琥珀暂无独立条目。'
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
  family: {
    title: '家族',
    groups: [
      {
        label: '家系',
        items: ['橡木家系', '猎犬家系', '苜蓿家系', '鸢尾花家系']
      }
    ],
    note: '匹诺康尼由五大家系共治，官方尚未完整公开全部家系。'
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
  },
  amphoreus: {
    title: '翁法罗斯',
    groups: [
      {
        label: '十二泰坦',
        items: [
          '艾格勒',
          '吉奥里亚',
          '法吉娜',
          '欧洛尼斯',
          '塔兰顿',
          '雅努斯',
          '墨涅塔',
          '刻法勒',
          '瑟希斯',
          '扎格列斯',
          '尼卡多利',
          '塞纳托斯'
        ]
      },
      {
        label: '黄金裔',
        items: [
          '阿格莱雅',
          '缇宝',
          '万敌',
          '遐蝶',
          '那刻夏',
          '风堇',
          '赛飞儿',
          '白厄',
          '海瑟音',
          '刻律德菈',
          '长夜月',
          '丹恒·腾荒',
          '昔涟'
        ]
      },
      {
        label: '相关',
        items: ['铁墓', '来古士']
      }
    ],
    note: '十二泰坦各持一枚火种；昔涟为第十三黄金裔。'
  },
  paradise: {
    title: '二相乐园',
    groups: [
      {
        label: '相关人物',
        items: ['开拓者', '星期日', '火花', '爻光', '不死途', '绯英', '真珠', '归寂', '虚照']
      },
      {
        label: '相关势力',
        items: ['星际和平公司', '假面愚者', '巡海游侠', '星穹列车', '悲悼伶人']
      }
    ],
    note: '幻月游戏每届八位谒者，名单随剧情推进而变化。'
  }
}

export default navboxes

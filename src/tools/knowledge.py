"""知识库工具（mock时空RAG + 知识图谱查询，Day 1 演示用）"""


def query_knowledge(disease: str, cultivar: str = None) -> list[dict]:
    """模拟时空RAG + 知识图谱查询"""
    knowledge_base = {
        "茶炭疽病": [
            {"source": "中国农科院茶叶研究所·茶树病虫害防治手册2024",
             "snippet": "茶炭疽病由刺盘孢菌Colletotrichum属真菌侵染所致，"
                        "在高湿（>75%）+ 中温（20-28℃）环境下扩散迅速，"
                        "金牡丹、福鼎大白等品种较为易感。"},
            {"source": "福建省农业农村厅·2025年茶叶病害防治指南",
             "snippet": "春茶嫩芽期 + 连续阴雨 是主要诱因。建议在发病初期"
                        "（病斑直径<2mm时）用药，三唑类与甲氧基丙烯酸酯类"
                        "轮换使用，避免抗药性。"},
        ],
    }
    return knowledge_base.get(disease, [])

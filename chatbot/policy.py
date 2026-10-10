"""按《促进和规范数据跨境流动规定》判断出境路径。

数量比较放在代码里，供工具调用返回。模型只负责收集事实和解释结果。
"""

from __future__ import annotations

EXEMPTIONS = {
    "none",
    "trade",
    "overseas_roundtrip",
    "contract",
    "hr",
    "emergency",
    "ftz_outside_list",
}

PATH_LABELS = {
    "exempt": "免予申报数据出境安全评估、订立个人信息出境标准合同、通过个人信息保护认证",
    "standard_contract_or_certification": "订立个人信息出境标准合同，或通过个人信息保护认证",
    "security_assessment": "申报数据出境安全评估",
    "invalid": "当前事实还不能判断路径",
}

_PI_DUTIES = [
    "向个人告知境外接收方的名称或者姓名、联系方式、处理目的、处理方式、个人信息的种类以及个人向境外接收方行使权利的方式和程序",
    "在法律、行政法规要求取得同意时，取得个人的单独同意",
    "事先进行个人信息保护影响评估",
    "采取加密、访问控制和最小必要等安全措施",
    "发生或者可能发生数据安全事件时采取补救措施，并及时向省级以上网信部门和其他有关主管部门报告",
]

_DATA_DUTIES = [
    "履行数据安全保护义务，采取技术措施和其他必要措施保障出境安全",
    "未被有关部门、地区告知或者公开发布为重要数据的，不需要把该数据作为重要数据申报出境安全评估",
]


def classify(
    is_ciio: bool,
    is_important_data: bool,
    general_pi_count: int,
    sensitive_pi_count: int,
    exemption: str = "none",
) -> dict:
    """返回路径、依据和仍需履行的义务。"""
    is_ciio = _as_bool("is_ciio", is_ciio)
    is_important_data = _as_bool("is_important_data", is_important_data)
    general_pi_count = _as_count("general_pi_count", general_pi_count)
    sensitive_pi_count = _as_count("sensitive_pi_count", sensitive_pi_count)
    if exemption not in EXEMPTIONS:
        raise ValueError(f"exemption 必须是 {sorted(EXEMPTIONS)} 之一")

    inputs = {
        "is_ciio": is_ciio,
        "is_important_data": is_important_data,
        "general_pi_count": general_pi_count,
        "sensitive_pi_count": sensitive_pi_count,
        "exemption": exemption,
    }
    notes: list[str] = []
    has_pi = general_pi_count > 0 or sensitive_pi_count > 0

    if exemption == "trade" and (is_important_data or has_pi):
        notes.append("当前数据包含个人信息或重要数据，不能适用第三条，已改按其他规则判断。")
        exemption = "none"
    elif exemption == "trade":
        return _result(
            "exempt",
            ["第三条：国际贸易、跨境运输、学术合作、跨国生产制造和市场营销等活动中收集和产生的数据向境外提供，不包含个人信息或者重要数据的，免予三条路径。"],
            notes,
            inputs,
            pi_duties=False,
        )

    if exemption == "ftz_outside_list":
        notes.append("请先确认该数据不在本自贸试验区已备案的负面清单内。清单内数据按清单管理。重要数据通常会被列入清单。")
        return _result("exempt", ["第六条：自贸试验区内向境外提供负面清单外的数据，可以免予三条路径。"], notes, inputs, pi_duties=has_pi)

    if exemption == "overseas_roundtrip":
        if is_important_data:
            notes.append("第四条要求处理过程中没有引入重要数据。当前数据已被标记为重要数据，本豁免不成立。")
            return _result(
                "security_assessment",
                ["第七条：向境外提供重要数据，应当申报数据出境安全评估。"],
                notes,
                inputs,
                pi_duties=has_pi,
            )
        notes.append("适用第四条的前提是：个人信息在境外收集和产生，传到境内处理后再次出境，且处理过程中没有引入境内个人信息或者重要数据。人数只统计境内引入的部分；本工具把 exemption 视为该前提已经成立。")
        return _result(
            "exempt",
            ["第四条：境外收集产生的个人信息入境处理后再出境，处理中未引入境内个人信息或重要数据的，免予三条路径。"],
            notes,
            inputs,
            pi_duties=True,
        )

    if exemption in {"contract", "hr", "emergency"}:
        if is_important_data:
            notes.append("第五条覆盖的是个人信息，不包括重要数据。其中的重要数据仍要申报出境安全评估。")
            return _result("security_assessment", ["第七条：向境外提供重要数据，应当申报数据出境安全评估。第五条不能豁免重要数据。"], notes, inputs, pi_duties=has_pi)
        basis = {
            "contract": "第五条第一项：为订立、履行个人作为一方当事人的合同所必需，例如跨境购物、跨境寄递、跨境汇款、跨境支付、跨境开户、机票酒店预订、签证办理、考试服务等。",
            "hr": "第五条第二项：按照依法制定的劳动规章制度和依法签订的集体合同实施跨境人力资源管理，确需向境外提供员工个人信息。",
            "emergency": "第五条第三项：紧急情况下为保护自然人的生命健康和财产安全，确需向境外提供个人信息。",
        }[exemption]
        notes.append("该豁免只覆盖条文写明的“确需”范围。同一批出境里另有超出该范围的个人信息时，超出部分按数量门槛另行判断。")
        notes.append("第七条、第八条写明，属于第五条情形的从其规定，因此符合本项时不再按人数改走评估或标准合同。")
        return _result("exempt", [basis], notes, inputs, pi_duties=True)

    if is_ciio and (is_important_data or has_pi):
        return _result(
            "security_assessment",
            ["第七条第一项：关键信息基础设施运营者向境外提供个人信息或者重要数据，应当申报数据出境安全评估。"],
            notes,
            inputs,
            pi_duties=has_pi,
        )

    if is_important_data:
        return _result(
            "security_assessment",
            ["第七条第二项：关键信息基础设施运营者以外的数据处理者向境外提供重要数据，应当申报数据出境安全评估。"],
            notes,
            inputs,
            pi_duties=has_pi,
        )

    if not has_pi:
        basis = ["未向境外提供个人信息或重要数据，第七条规定的安全评估义务没有被触发。"]
        if not is_ciio:
            basis.append("若这些数据来自国际贸易、跨境运输、学术合作、跨国生产制造和市场营销等活动，同时符合第三条。")
        return _result("exempt", basis, notes, inputs, pi_duties=False)

    assessment_reasons = []
    if sensitive_pi_count >= 10000:
        assessment_reasons.append("自当年1月1日起累计向境外提供1万人以上敏感个人信息")
    if general_pi_count >= 1_000_000:
        assessment_reasons.append("自当年1月1日起累计向境外提供100万人以上个人信息（不含敏感个人信息）")
    if assessment_reasons:
        return _result(
            "security_assessment",
            ["第七条第二项：" + "；".join(assessment_reasons) + "，应当申报数据出境安全评估。"],
            notes,
            inputs,
            pi_duties=True,
        )

    scc_reasons = []
    if sensitive_pi_count > 0:
        scc_reasons.append("累计向境外提供敏感个人信息，且不满1万人")
    if general_pi_count >= 100_000:
        scc_reasons.append("累计向境外提供10万人以上、不满100万人个人信息（不含敏感个人信息）")
    if scc_reasons:
        notes.append("两条手续选一条完成即可：订立个人信息出境标准合同，或通过个人信息保护认证。")
        if sensitive_pi_count > 0 and general_pi_count < 100_000:
            notes.append("只要出境数据中含有敏感个人信息，就不能再用第五条第四项按“不满10万人”豁免。")
        return _result(
            "standard_contract_or_certification",
            ["第八条：" + "；".join(scc_reasons) + "，应当订立个人信息出境标准合同或者通过个人信息保护认证。"],
            notes,
            inputs,
            pi_duties=True,
        )

    return _result(
        "exempt",
        ["第五条第四项：关键信息基础设施运营者以外的数据处理者，自当年1月1日起累计向境外提供不满10万人个人信息（不含敏感个人信息），免予三条路径。"],
        notes,
        inputs,
        pi_duties=True,
    )


def render(result: dict) -> str:
    lines = [
        f"结论：{result['path_label']}",
        "依据：",
        *[f"- {item}" for item in result["basis"]],
    ]
    if result["notes"]:
        lines.append("判断时请一并核对：")
        lines.extend(f"- {item}" for item in result["notes"])
    lines.append("出境个人信息时仍要做：")
    lines.extend(f"- {item}" for item in result["still_required"])
    lines.append("来源：《促进和规范数据跨境流动规定》（国家互联网信息办公室令第16号，2024年3月22日起施行）")
    return "\n".join(lines)


def _result(path: str, basis: list[str], notes: list[str], inputs: dict, pi_duties: bool) -> dict:
    duties = list(_PI_DUTIES if pi_duties else _DATA_DUTIES)
    return {
        "path": path,
        "path_label": PATH_LABELS[path],
        "basis": basis,
        "notes": notes,
        "still_required": duties,
        "inputs": inputs,
        "source": "《促进和规范数据跨境流动规定》 https://www.cac.gov.cn/2024-03/22/c_1712776611775634.htm",
    }


def _as_bool(name: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} 必须是 true 或 false")
    return value


def _as_count(name: str, value: object) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} 必须是非负整数")
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} 必须是非负整数")
    return value

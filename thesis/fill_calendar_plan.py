import shutil
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET


def set_cell_text(tc: ET.Element, text: str, ns: dict) -> None:
    # Remove existing paragraphs and replace with a single paragraph/run/text.
    for p in list(tc.findall("./w:p", ns)):
        tc.remove(p)
    p = ET.SubElement(tc, f"{{{ns['w']}}}p")
    r = ET.SubElement(p, f"{{{ns['w']}}}r")
    t = ET.SubElement(r, f"{{{ns['w']}}}t")
    if text.startswith(" ") or text.endswith(" "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text


def main() -> None:
    src = Path(r"C:\Users\Daka\Desktop\VKR_MAIN\thesis\Календарный план.docx")
    dst = src.with_name("Календарный план (заполненный).docx")

    shutil.copyfile(src, dst)

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    with zipfile.ZipFile(dst, "r") as z:
        xml_bytes = z.read("word/document.xml")

    root = ET.fromstring(xml_bytes)

    tbl = root.find(".//w:tbl", ns)
    if tbl is None:
        raise RuntimeError("Не найдена таблица в шаблоне.")

    trs = tbl.findall("./w:tr", ns)
    if len(trs) < 2:
        raise RuntimeError("В таблице нет строк с этапами.")

    plan = {
        "1.": {
            "stage": "Утверждение темы ВКР и научного руководителя. Составление и согласование индивидуального плана.",
            "result": "Подписанный календарный план и закрепленная тема ВКР.",
            "due": "01.02.2026",
            "fact": "Выполнено (тема утверждена; план практики 13.04.2026)",
        },
        "2.": {
            "stage": "Сбор, изучение и анализ научной литературы по теме исследования.",
            "result": "Список литературы (не менее 10 источников) + оформленный вариант по требованиям кафедры.",
            "due": "10.03.2026",
            "fact": "Выполнено (списки: 26, 27)",
        },
        "3.": {
            "stage": "Написание теоретической (аналитической) части ВКР (Глава 1).",
            "result": "Текст главы 1 (примерно 15–20 стр.), согласованный с научным руководителем.",
            "due": "31.03.2026",
            "fact": "Выполнено (глава 1 в финальном тексте)",
        },
        "4.": {
            "stage": "Проектирование архитектуры системы и структуры данных (Глава 2: 2.1–2.4).",
            "result": "ER-диаграмма, блок-схема архитектуры, описание сущностей, интерфейсов и API-контуров.",
            "due": "19.04.2026",
            "fact": "Выполнено (практика: 15–19.04.2026)",
        },
        "5.": {
            "stage": "Практическая реализация: сервер API + БД + интеграция с n8n + desktop/mobile клиенты.",
            "result": "Работоспособный прототип системы (API, клиенты), интеграция с n8n, хранение артефактов.",
            "due": "02.05.2026",
            "fact": "Выполнено (практика до 02.05.2026)",
        },
        "6.": {
            "stage": "Тестирование и проверка сценариев работы системы. Сбор и обработка результатов.",
            "result": "Набор тестов/сценариев, таблица проверок, скриншоты/логи подтверждения работоспособности.",
            "due": "04.05.2026",
            "fact": "Выполнено (практика: 04.05.2026)",
        },
        "7.": {
            "stage": "Написание практической части ВКР (Главы 2, 3) по реализации и тестированию.",
            "result": "Текст глав 2–3 (примерно 25–35 стр.) с описанием реализации, архитектуры и результатов.",
            "due": "15.05.2026",
            "fact": "Выполнено (финальный текст сформирован)",
        },
        "8.": {
            "stage": "Оформление ВКР: введение/заключение, список литературы, приложения, рисунки, единый стиль.",
            "result": "Полный текст ВКР, оформленный по методичке; готовые приложения (код/скриншоты).",
            "due": "20.05.2026",
            "fact": "Выполнено (финальная версия .docx)",
        },
        "9.": {
            "stage": "Проверка работы в системе «Антиплагиат», устранение некорректных заимствований.",
            "result": "Отчет о проверке с допустимым процентом уникальности; при необходимости — исправления.",
            "due": "01.05.2026",
            "fact": "Выполнено (проверка: 01.05.2026)",
        },
        "10.": {
            "stage": "Предзащита на кафедре. Устранение замечаний.",
            "result": "Положительный результат предзащиты; внесенные правки в текст/презентацию.",
            "due": "25.05.2026",
            "fact": "",
        },
        "11.": {
            "stage": "Подготовка презентации и текста доклада для защиты.",
            "result": "Презентация 12–15 слайдов + отрепетированный доклад 7–8 минут.",
            "due": "05.06.2026",
            "fact": "",
        },
        "12.": {
            "stage": "Защита выпускной квалификационной работы перед ГЭК.",
            "result": "Протокол ГЭК с оценкой.",
            "due": "20.06.2026",
            "fact": "",
        },
    }

    # Iterate rows except header row.
    for tr in trs[1:]:
        tcs = tr.findall("./w:tc", ns)
        if len(tcs) < 5:
            continue

        cell_text = "".join([t.text or "" for t in tcs[0].findall(".//w:t", ns)]).strip()
        if cell_text not in plan:
            continue

        data = plan[cell_text]
        set_cell_text(tcs[1], data["stage"], ns)
        set_cell_text(tcs[2], data["result"], ns)
        set_cell_text(tcs[3], data["due"], ns)
        set_cell_text(tcs[4], data["fact"], ns)

    # xml.etree in some Python builds doesn't support standalone= in tostring().
    new_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    with zipfile.ZipFile(dst, "a") as z:
        z.writestr("word/document.xml", new_xml)

    print(dst)


if __name__ == "__main__":
    main()


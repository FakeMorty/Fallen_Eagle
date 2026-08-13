#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор игровых файлов событий AoH2:DE из структур дизайна (Эпоха 1).

Порождает текстовый формат (старая система событий, которую DE читает).
Точные токены исходов сверяй с game/_FAQ/Events_Outcomes.txt.
"""
import os, re
from gen_design import EVENTS

# ------------------ slug для id ------------------
def slug(s):
    s = s.lower()
    s = re.sub(r"[«»\"'`]", "", s)
    s = re.sub(r"[^\w]+", "_", s)
    s = s.strip("_")
    return s

# ------------------ исходы по цвету (ЗАГЛУШКИ — реальные числа подбирает автор) ------------------
# 'r' = консерватор/жёсткий (риск, сила), 'y' = центрист, 'g' = реформатор
COLOR_OUTCOMES = {
    'r': ["stability=2", "gold=-100", "# консервативный курс: стабильность ценой реформ"],
    'y': ["stability=1", "gold=-30",  "# центристский курс"],
    'g': ["stability=-1", "growth_rate=2", "# реформаторский курс: риск, но рост"],
}

TAG = "ssr"  # тег СССР (заглушка — подставь реальный тег цивилизации)

def emit_event(f, eid, title, desc, triggers, options):
    """options = list of (button_name, [outcome lines])"""
    f.write(f"id={eid}\n")
    f.write(f"title={title}\n")
    f.write(f"desc={desc}\n")
    for t in triggers:
        f.write(f"{t}\n")
    f.write(f"is_civ={TAG}\n")
    f.write("\n")
    for (name, outcomes) in options:
        f.write(f"option_btn name={name}\n")
        for o in outcomes:
            f.write(f"{o}\n")
        f.write("option_end\n\n")

def main():
    outdir = "/home/user/game/events/common"
    os.makedirs(outdir, exist_ok=True)

    manifest = []
    idx = 1
    for e in EVENTS:
        year = e['year']
        title = e['title']
        base = f"ussr{year}_{slug(title)}"
        fname = f"{base}.txt"
        with open(os.path.join(outdir, fname), "w", encoding="utf-8") as f:
            # --- РОМБ: главное событие с 3 решениями ---
            options = []
            for (color, label, arc) in e['decisions']:
                lab = slug(label)
                # решение ставит метку (id события запомнится) и запускает свою дугу
                first = f"{base}_{lab}_1"   # НАЧАЛО дуги
                options.append((label, COLOR_OUTCOMES[color] + [f"trigger_event={first}"]))
            emit_event(f, base, f"{year} · {title}",
                       f"Событие {title} ({year}). Выберите курс.",
                       [f"year_over={int(year)-1}", f"year_below={int(year)+1}"],
                       options)

            # --- ДУГИ: ①→②→③ для каждого решения ---
            for (color, label, arc) in e['decisions']:
                lab = slug(label)
                stages = ["1", "2", "3"]
                stage_names = {s[0]: s for s in arc}  # (НАЧАЛО, КУЛЬМИНАЦИЯ, ФИНАЛ)
                for i, (stage, subtitle, choices) in enumerate(arc):
                    eid = f"{base}_{lab}_{stages[i]}"
                    nxt = f"{base}_{lab}_{stages[i+1]}" if i < 2 else None
                    opts = []
                    for (cc, txt) in choices:
                        outs = list(COLOR_OUTCOMES[cc])
                        if nxt:
                            outs.append(f"trigger_event={nxt}")
                        opts.append((txt, outs))
                    emit_event(f, eid, f"{stage} · {subtitle}",
                               f"{stage}: {subtitle} (дуга решения «{label}»).",
                               [f"has_variable={base}"],  # срабатывает, только если выбрали это решение
                               opts)
        manifest.append((year, title, fname))

    # манифест
    with open("/home/user/game/events/MANIFEST.md", "w", encoding="utf-8") as mf:
        mf.write("# Манифест событий Эпохи 1 (AoH2:DE)\n\n")
        mf.write("| Год | Событие | Файл |\n|---|---|---|\n")
        for (y, t, fn) in manifest:
            mf.write(f"| {y} | {t} | `{fn}` |\n")
        mf.write("\n> ID цивилизации и числовые исходы — заглушки. Сверь токены с game/_FAQ/Events_Outcomes.txt.\n")

    print(f"Сгенерировано событий-файлов: {len(manifest)}")
    print("Папка: /home/user/game/events/common/")
    for (y, t, fn) in manifest[:5]:
        print(f"  {y} · {t} → {fn}")

if __name__ == "__main__":
    main()

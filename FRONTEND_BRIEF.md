# FlameAtlas — бриф для фронтенда

> **Для Claude (или любого ассистента), который помогает с фронтендом:** прочитай этот файл целиком до того, как менять код. Здесь описано, какие файлы твои, какие трогать нельзя и как работать в git, чтобы потом всё слилось без конфликтов.

## Что за проект

**FlameAtlas** — веб-дашборд для NASA Space Apps Challenge 2026, челлендж **«Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data»**.

Задача челленджа: интерактивный AI-дашборд, который **summarizes, ranks and interprets** эксперименты NASA по горению в микрогравитации (база PSI) и выдаёт выводы по пожарной безопасности для кораблей, станций, лунных и марсианских баз и герметичных роверов.

**Аудитория:** профессора, аспиранты, студенты, аэрокосмические инженеры. Значит, стиль серьёзный и научный, не «игрушечный»: точные параметры, единицы измерения, ссылки на источники.

**Команда из двух человек:**
- **Data & AI** (Абдулла): извлечение данных из PDF, ранжирование, AI-выводы, чат. Папка `src/flameatlas/` и `scripts/`.
- **Product & Frontend** (ты): интерфейс, дизайн, графики, онбординг, питч.

## Стек (не менять)

- **Python + Streamlit**, запуск: `streamlit run app.py`
- Графики: **Plotly** (`plotly.express` / `plotly.graph_objects`)
- Никакого React или отдельного бэкенда: нет времени, и деплой будет на Streamlit Community Cloud.
- Новые библиотеки добавлять только при реальной необходимости, и сразу дописывать их в `requirements.txt`.

## Кто какие файлы трогает (главное правило для лёгкого мерджа)

| Файл / папка | Владелец | Можно менять фронтенду? |
|---|---|---|
| `app.py` | **Frontend** | ✅ Да, это твой главный файл |
| `ui/` (создай сам) | **Frontend** | ✅ Да: свои компоненты, страницы, хелперы |
| `assets/` (создай сам) | **Frontend** | ✅ Да: картинки, CSS, логотип |
| `.streamlit/config.toml` (создай сам) | **Frontend** | ✅ Да: тема, цвета, шрифт |
| `src/flameatlas/ui_ai.py` | Data & AI | ⚠️ Только импортировать и вызывать. Если нужно изменить, попроси Абдуллу |
| `src/flameatlas/*.py` (остальное) | Data & AI | ❌ Нет |
| `scripts/*` | Data & AI | ❌ Нет |
| `data/*` | Data & AI | ❌ Нет (только читать) |
| `requirements.txt` | общий | ✅ Только **добавлять** строки в конец |
| `README.md` | общий | ✅ Раздел «Screenshots / How to use» |

Если нужна новая функция данных (например, другой график требует агрегации), **напиши её в `ui/`**, читая готовый `DataFrame`. В `src/flameatlas/` её не клади.

## Как работать в git

```bash
git clone https://github.com/qwepablo12/Flame_Atlas.git
cd Flame_Atlas
git checkout -b frontend          # работай ТОЛЬКО в этой ветке
# ... работа ...
git add app.py ui/ assets/ .streamlit/ requirements.txt
git commit -m "UI: <что сделал>"
git push -u origin frontend
```

- **Каждые 1–2 часа** подтягивай свежие данные и AI от Абдуллы: `git pull origin main`. Если файлы распределены по таблице выше, конфликтов не будет.
- Когда фича готова, открой **Pull Request** `frontend → main` на GitHub. Абдулла смёрджит.
- **Никогда не коммить `.env`** (там API-ключ). Он уже в `.gitignore`.
- Не делай `git add .`, если сгенерировал что-то в `data/`: добавляй только свои файлы.

## Установка

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # ключ ANTHROPIC_API_KEY возьми у Абдуллы (не публикуй!)
streamlit run app.py
```

Без ключа дашборд тоже работает, только AI-вкладки показывают подсказку «Add ANTHROPIC_API_KEY». Вёрстку можно делать и без ключа.

## Данные, которые уже есть

**`data/processed/experiments.csv`** — 137 реальных тестов из 9 документов NASA (BASS-II, FLEX, Saffire и др.). Одна строка = одно условие теста. Колонки:

| Колонка | Что это |
|---|---|
| `test_id` | `T0001`… На них ссылаются AI-ответы вида `[T0012]` |
| `investigation` | Эксперимент: `BASS-II`, `FLEX`, `SAFFIRE-II`… |
| `hardware`, `platform`, `year` | Установка (MSG, CIR/MDCA, Cygnus), платформа, год |
| `category` | `prevention` / `detection` / `suppression` / `fundamental` / `unknown` |
| `objective` | Цель теста |
| `fuel`, `phase`, `sample_geometry` | Топливо/материал, фаза (`solid`/`liquid`/`gas`/`aerosol`), форма образца |
| `pressure_kpa`, `o2_percent`, `diluent`, `flow_speed_cm_s`, `gravity_g` | Условия (**могут быть пустыми**, т.е. NaN) |
| `outcome` | `ignited_spread`, `ignited_no_spread`, `no_ignition`, `extinguished`, `detected`, `other`, `unknown` |
| `spread_rate_mm_s` | Скорость распространения пламени (заполнено редко) |
| `measurements`, `key_finding`, `quote` | Датчики, главный вывод, **дословная цитата** из источника |
| `source_title`, `source_url`, `page` | Источник и страница |
| `confidence` | 0–1, насколько уверенно извлечено |
| `psi_id`, `psi_url` | ID и страница исследования в PSI (для цитирования) |

**`data/processed/experiments_mock.csv`** — фейковые данные той же структуры (для тестов вёрстки).
**`data/psi_catalog.csv`** — каталог 26 исследований PSI по горению (через `load_catalog()`: 25, без одного нерелевантного).

⚠️ **Многие числовые поля пустые.** Любой график обязан делать `dropna()` по своим колонкам и не падать на пустых данных.

## Готовые функции (импортируй, не переписывай)

```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from flameatlas.missions import MISSIONS
# dict: "Earth / ISS cabin", "Moon base / pressurized rover", "Mars habitat (assumed same as Moon)", "Spacesuit"
# каждый -> {"pressure_kpa", "o2_percent", "gravity_g", "note"}

from flameatlas.rank import rank, gravity_bounds
# rank(df, target, top=10) -> df с колонкой "relevance" (0..1), отсортирован
#   target = {"o2_percent", "pressure_kpa", "flow_speed_cm_s", "gravity_g", "phase" (None или "solid"/...)}
# gravity_bounds(df, target) -> {"microgravity": df, "normal_gravity": df}  # 0 g и 1 g как границы для Луны/Марса

from flameatlas.catalog import load_catalog
# DataFrame: psi_id, title, url, type, objectives, approach, acronym, category, hardware, relevance_tier (1..3)

from flameatlas.ui_ai import render_insight, render_chat, render_compare, render_investigations
# render_insight(top, mission_name, target, df)  — карточка AI-вывода (кнопка + markdown + cited tests + sources)
# render_chat(df)                                — чат-вопросы по документам
# render_compare(df)                             — сравнение двух экспериментов
# render_investigations(df)                      — таблица всех исследований PSI
```

Эти четыре `render_*` — готовые блоки. Ставь их куда угодно в лэйауте (вкладки, колонки, отдельные страницы), оборачивай в свои контейнеры и заголовки. Внутрь не лезь.

## Что сделать (по приоритету)

### P0: обязательно
1. **Лэйаут главного экрана.** Слева сайдбар: пресет миссии, ползунки O₂ / давление / поток, фаза топлива. В центре топ похожих тестов с колонкой relevance (как бар) и 1–2 графика. Ниже вкладки с AI-блоками.
2. **Шапка / онбординг.** Одна строка «что это» плюс 3 шага «выбери среду → посмотри похожие эксперименты → получи AI-вывод с источниками». Можно `st.expander("How to use")`.
3. **Карточки пресетов.** Показать параметры выбранной среды (O₂, давление в kPa и psi, гравитация) метриками `st.metric`, а для Луны/Марса пометку «нет данных при частичной гравитации, используем 0 g и 1 g как границы».
4. **Тема.** `.streamlit/config.toml`, тёмная, акцентный цвет «пламя» (оранжево-красный), читаемая.
5. **Футер с цитированием:** «Data: NASA Physical Sciences Informatics (PSI). Cite each investigation via its DOI on its PSI page.»

### P1: сильно усиливает
6. **Графики** (Plotly, с подписями осей и единицами):
   - **Карта воспламеняемости:** x = `flow_speed_cm_s`, y = `o2_percent`, цвет = `outcome`, форма = `investigation`, плюс крестик в точке выбранной среды.
   - **O₂ по экспериментам:** strip/box plot `o2_percent` по `investigation`.
   - **0 g vs 1 g:** из `gravity_bounds()`, две колонки или сгруппированный график.
   - Сейчас график «Spread rate vs O2» почти пустой (`spread_rate_mm_s` редко заполнен). Замени его или оставь вторым.
7. **Фильтры:** по `investigation`, `category`, `phase` (мультиселект), и чтобы все графики и таблица на них реагировали.
8. **Вкладка «On Earth»** — польза для Земли (челлендж прямо это предлагает): 3–4 карточки по ресурсам челленджа: тонкодисперсные водяные огнетушители с МКС, детектор дыма шаттла (отличает дым от пыли), воздушные баллоны пожарных из технологий скафандров, ткань для защитной одежды пожарных. Короткий текст плюс ссылка на ресурс со страницы челленджа.
9. **Карточка теста** при выборе строки в таблице: все поля, цитата крупно, ссылки на PSI и статью.

### P2: если останется время
10. Главная находка на первом экране: «В BASS-II PMMA устойчиво горел при **13.6% O₂** в микрогравитации, тогда как на Земле гаснет при **16%** → земные тесты не консервативны для космоса» (подтверждено цитатой в данных; найди строку с 13.6 в `experiments.csv`).
11. Страница «About / Method»: схема пайплайна (PDF → извлечение → ранжирование → AI с цитатами), список источников из `data/sources.csv`.
12. Мобильная ширина: ничего не должно ломаться.

## Критерии готовности

- `streamlit run app.py` запускается без ошибок и предупреждений (никаких `use_container_width`, используй `width="stretch"`).
- Работает и на `experiments.csv`, и на `experiments_mock.csv`, и с пустыми NaN.
- Без API-ключа AI-вкладки показывают подсказку, а не падают.
- Изменены только файлы из колонки «Frontend» таблицы владения.
- Скриншоты главного экрана добавлены в `README.md`.

## Не делай

- Не переименовывай колонки и не меняй `src/flameatlas/*`.
- Не добавляй регистрацию, аккаунты, базы данных.
- Не выдумывай данные и цифры в интерфейсе: только то, что есть в CSV или в ресурсах челленджа.
- Не хардкодь API-ключ в коде.

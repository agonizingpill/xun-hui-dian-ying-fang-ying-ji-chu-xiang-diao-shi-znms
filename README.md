# 岚幕巡回放映 · 出箱调试

岚幕放映车队为三处礼堂和露天场地安排流动放映。车上保留不同卡口的备用镜头。到场先签电气回执，再跑校准卡。软焦时领镜头，换镜后必须对原异常片段复测，才能签开放映。

## 班组与现状

模拟客户是 9 人岚幕放映车队，其中放映员轮流跑点，器材员保管镜头套箱。原来使用放映日志、现场电表纸单和纸箱领条。三类掉链延误最多，未签接电就开机、镜头领错卡口、拿换镜前一张校准单签开场。场地接电记录给当值放映员，画质检验供器材环节分流，签发结果交给开场和值守人员。

| 角色 | 演示账号 | 职责 |
|---|---|---|
| 作业员 | `operator@demo.test` | 录入电气实测，运行并签入校准判别 |
| 复核员 | `reviewer@demo.test` | 另可发备用镜头、复核归箱和签放 |
| 只读访客 | `viewer@demo.test` | 核对场地、器材状态、检测和放映交班 |

演示密码均为 `DemoC0de!2026`。

## 启动

```bash
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

前端在 `http://localhost:18311`，后端文档在 `http://localhost:19311/docs`。MySQL 宿主端口 17811，库名和账户均为 `desk`。停止命令为 `docker compose down`，增加 `-v` 会移除本项目数据。

| 服务 | 技术与职责 |
|---|---|
| frontend | Nginx，原生 HTML/CSS/JavaScript，对后端同源转发 |
| backend | Python 3.11、FastAPI、Pydantic、SQLAlchemy |
| worker | Redis 驱动的 scikit-learn ExtraTrees 分类 |
| db | MySQL 8，放映位、插座回执、校准检测、镜头与领用 |
| redis | 计算请求、计算结果和心跳 |

`.env.example` 列出容器名、三个映射端口、`DB_PASSWORD`、`JWT_SECRET` 与 `SEED_DEMO`。日常开发在 `backend/` 安装本地依赖，并设置 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`。可运行 `uvicorn core.app:app --port 8000` 与 `python -m core.worker`。

## 一次巡回作业

1. 18:00，放映员到藤川南场，用配电箱 `BOX-03` 检查 `LM-SOUTH` 的 19:30 场。
2. 18:02，电压 221 V，若未确认接地，保留拒绝回执并阻止现场跑校准卡。
3. 18:10，重新获得接地确认后签下有效回执，使用卡 `GRID-41` 的四个归一值检测。
4. 18:15，检测单 `RD-1124-SOFT` 的轮廓损失 0.79，判为软焦。EF 备用镜头不能安装到本机 PL 口。
5. 18:25，复核员出箱 `LEN-PL-35`，光学版号增加。换镜前的检测立刻失效。
6. 18:40，在同一校准卡上重复测量，引用原检测号。轮廓损失 0.11、色偏 0.12、闪变 0.10、帧间波动 0.08。
7. 18:45，当前电气及光学版的干净分类达到 80% 门槛，复核员签放。场地交班看到检测凭据。
8. 21:30，扫箱签 `CASE-P35` 归箱，镜头恢复可借用，工位需重新验电。

## 模型、接口与结构

`backend/domain/learning.py` 使用固定随机种子模拟四类校准卡读数，共 220 条训练和独立种子生成的 60 条留出记录。特征为轮廓损失、色彩偏差、亮度闪变和帧间波动。96 棵极端随机树拟合标签，类概率由各树概率平均生成。模型以版本号和概率分布落库。基准样例的准确率衡量模拟输入，现场应用需要独立采样校准。

- `backend/domain/booth_tables.py`、`lens_tables.py` 声明业务表及约束。
- `outlet.py` 签收新电气版；`measurement.py` 固定当期校准卡和原记录；`spares.py` 管理镜头出箱与归还；`call_sheet.py` 检查权限、版本和放映阈值。
- `frontend/src/pages/` 提供电气、校准、器材和放映交班。
- 角色在 `backend/core/roles.py` 与 `frontend/src/store.js`。工位、镜头、借用和标签枚举在 `backend/domain/states.py` 与 `frontend/src/booth-state.js`，重复用于 SQL 约束和各页的状态显示。

源码使用 MIT 许可，见 `LICENSE`。

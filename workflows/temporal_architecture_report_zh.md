# 架构决策报告：为什么选择 Temporal 而非 Dapr/EventBus？

## 1. 核心理念对比

我们在项目中探讨了两种截然不同的架构模式。以下是为什么 **Temporal (编排模式)** 比你最初设想的 **Dapr/Sidecar (编舞模式)** 更适合 HoloAssetManagement 的深度分析。

### 方案 A：你最初的设想 (Dapr + Event Bus)
*   **模式**：编舞 (Choreography)
*   **隐喻**：“把瓶子扔进大海”。
    *   登录服务发出 `UserLoggedIn` 事件。
    *   它**不知道**谁会处理，也**不关心**处理结果。
    *   邮件服务、分析服务各自订阅这个事件。
*   **痛点**：
    *   **运维地狱**：引入 Dapr 意味着每个服务旁边都要跑一个 Sidecar 进程。你还需要维护 Redis 或 Kafka 作为底层消息队列。
    *   **上帝视角的缺失**：想知道“登录后到底发生了什么”？你无法通过看代码知道。你必须去查文档、查配置、或者在分布式链路追踪系统中在大海捞针。
    *   **一致性难题**：如果“发邮件”失败了怎么办？登录服务已经发完事件不管了。你需要额外的死信队列 (DLQ) 处理逻辑。要保证“数据库写入”和“发消息”同时成功，你甚至需要实现复杂的 **Outbox Pattern**。

### 方案 B：我们实现的方案 (Temporal Orchestration)
*   **模式**：编排 (Orchestration)
*   **隐喻**：“指挥家与乐团”。
    *   `UserLoginWorkflow` 作为一个中心指挥者。
    *   它**显式地调度**：先做 A，同时做 B 和 C，等都做完了再做 D。
*   **优势**：
    *   **代码即真理 (Code is Truth)**：打开 `login_example.py`，逻辑一目了然：`await asyncio.gather(email, analytics)`。没有任何隐藏逻辑。
    *   **架构极简 (KISS)**：不需要 Sidecar，不需要 Kafka，不需要 Outbox。Temporal Server + 你的 Python 代码就是全部。
    *   **强一致性保障**：Temporal 保证“只要代码写了，就一定会执行”。如果分析服务挂了，Workflow 会自动重试，直到服务恢复。你不需要写一行重试代码。

---

## 2. 具体场景分析

### 场景一：Pizza 订单 (长流程与状态)
*   **旧思路**：用 MQ 发消息 -> 消费者存数据库状态 `STATUS=DOUGH_MADE` -> 写个 CronJob 每分钟扫表看看是不是过了 10 秒 -> 发下一个 MQ。
*   **Temporal**：
    ```python
    await workflow.execute_activity(make_dough)
    await asyncio.sleep(10)  # 这里是持久化的，服务器重启也没事
    await workflow.execute_activity(bake_pizza)
    ```
    **结论**：Temporal 把复杂的**分布式状态机**变成了一个简单的**Python 函数**。

### 场景二：登录后的插件化操作 (并行与解耦)
*   **旧思路**：Event Bus 解耦。
*   **Temporal**：显式并行 + 动态调度。
    ```python
    # 既保留了解耦 (通过配置加载插件列表)，又保留了控制力 (等待所有插件执行完)
    await asyncio.gather(*[workflow.execute_activity(plugin) for plugin in plugins])
    ```
    **结论**：我们获得了 Event Bus 的灵活性，但没有失去系统的**可观测性**。

---

## 3. 最终结论 (The Verdict)

对于 HoloAssetManagement 这样的系统：

1.  **做减法**：放弃 Dapr。在这个阶段引入 Sidecar 只会增加部署和调试的复杂度，收益极低。
2.  **拥抱确定性**：使用 Temporal。相比于“发后即忘 (Fire-and-forget)”的消息队列，业务系统通常更需要“保证完成 (Guaranteed Execution)”的工作流。
3.  **开发者体验**：你会发现，写 Python 代码 (Workflow) 远比写 YAML 配置 (Dapr Components) 和调试网络问题要快乐得多。

**Temporal 不仅仅是一个库，它是你构建分布式系统的“降维打击”武器。**

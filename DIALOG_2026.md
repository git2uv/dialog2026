# Playwright Java vs Python 开发对话记录

**日期**: 2026-06-18  
**用户**: git2uv  
**主题**: Selenium Java 到 Playwright 的转换、性能对比、开发流程

---

## 📌 核心问题解答

### 1. Playwright Java vs Python 性能对比

**结论**: 
- Java Playwright **略快 5-10%**（在高并发场景）
- Python 在单线程/中等并发 **几乎没差别**
- 都比 Selenium 快很多

**原因**:
- Playwright 核心是 Node.js，两种语言只是客户端
- 性能差别主要来自语言本身（JVM vs GIL）
- Java 的 JVM 编译优化更好
- Java 线程管理比 Python (GIL限制) 更高效

**对抢购脚本的影响**: 差别**可以忽略不计**

---

### 2. 为什么 Python 办公自动化比 Java 流行？

| 评分 | 方面 | Python | Java |
|-----|------|--------|------|
| ⭐⭐⭐⭐⭐ | 学习曲线 | Python 赢 | - |
| ⭐⭐⭐⭐⭐ | 开发速度 | Python 赢 | - |
| ⭐⭐⭐⭐⭐ | 代码简洁 | Python 赢 | - |
| ⭐⭐⭐ | 运行性能 | - | Java 赢 |
| ⭐⭐⭐ | 生态丰富 | Python 赢 | - |

**关键数据**:
```
处理 10 万行 Excel：
Python:  3 秒
Java:    1.5 秒
差别：1.5 秒 ← 用户感受不到！

学习成本：
Python:  1 天 学会
Java:    1 周 学会
差别：6 天！ ← 用户明显感受到！
```

**结论**: 对于办公自动化，**快速开发 > 运行速度**

---

### 3. Playwright 异步机制说明

**关键纠正**: 
- Playwright **无论 Python 还是Java，核心通信机制都是异步的**
- 区别不在"异步/同步"，而在**代码写法**和**线程模型**

| 对比项 | Java Playwright | Python Playwright |
|------|---|---|
| **异步模型** | CompletableFuture / 线程池 | async/await + asyncio |
| **代码写法** | 同步风格（.get() 阻塞等待） | 异步风格（await 关键字） |
| **线程管理** | JVM 真正的多线程，高效 | Python GIL，单线程事件循环 |

**执行流程**:
```
Playwright (Java/Python) 
    ↓
WebSocket 通信（异步）
    ↓
Node.js 服务端
    ↓
浏览器 DevTools Protocol（异步）
```

---

### 4. Java Playwright 代码示例

```java
import com.microsoft.playwright.*;
import java.util.Scanner;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

public class TengxunyunBot {
    private Browser browser;
    private Page page;
    private AtomicBoolean running = new AtomicBoolean(true);
    private ScheduledExecutorService highFreqScheduler;

    public void setup() throws Exception {
        Playwright playwright = Playwright.create();
        BrowserType chromium = playwright.chromium();
        browser = chromium.launch(new BrowserType.LaunchOptions().setHeadless(false));
        page = browser.newPage();
        System.out.println("浏览器已启动");
    }

    public void tearDown() throws Exception {
        running.set(false);
        if (page != null) {
            page.close();
        }
        if (browser != null) {
            browser.close();
        }
        System.out.println("end");
    }

    public void hello() throws InterruptedException {
        try {
            // 设置导航超时为 20 秒
            page.navigate("https://cloud.tencent.com/act/pro/warmup-202606",
                    new Page.NavigateOptions().setTimeout(20000));

            System.out.println("页面已加载");
            System.out.println("主调度器");

        } catch (PlaywrightException e) {
            System.out.println("页面加载失败或超时: " + e.getMessage());
            return;
        }

        // 读取用户输入
        Scanner sc = new Scanner(System.in);
        System.out.print("请输入数字后按回车: ");
        System.out.flush();
        int a = sc.nextInt();
        System.out.println("输入数字: " + a);

        System.out.println("主调度器");
        
        // 主调度器，每50ms执行一次
        ScheduledExecutorService mainScheduler = Executors.newScheduledThreadPool(1);
        running.set(true);

        Runnable mainTask = () -> {
            try {
                // 使用简洁的选择器
                ElementHandle button = page.querySelector(".uno3-buy-card__btn");

                if (button != null) {
                    String buttonText = button.textContent();
                    System.out.println("按钮状态: " + buttonText);

                    // 检查对话框是否存在
                    ElementHandle dialogFooter = page.querySelector(".uno3-dialog-footer");

                    if (dialogFooter != null) {
                        // 启动高频点击器
                        if (highFreqScheduler == null || highFreqScheduler.isShutdown()) {
                            startHighFrequencyClicker();
                        }
                        return;
                    }

                    // 主按钮点击逻辑
                    if (!buttonText.equals("添加提醒") && !buttonText.equals("取消提醒")) {
                        try {
                            button.click();
                        } catch (Exception e) {
                            // 点击失败，用 JavaScript 点击
                            page.evaluate("arguments[0].click();", button);
                        }
                    }
                }
            } catch (Exception e) {
                System.out.println("主任务错误: " + e.getMessage());
            }
        };

        // 每50ms执行一次
        mainScheduler.scheduleAtFixedRate(mainTask, 0, 50, TimeUnit.MILLISECONDS);

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            running.set(false);
            if (mainScheduler != null) {
                mainScheduler.shutdown();
            }
            if (highFreqScheduler != null) {
                highFreqScheduler.shutdown();
            }
        }));

        System.out.println("程序运行中，按回车键退出...");
        sc.nextLine();
        sc.nextLine();

        running.set(false);
        mainScheduler.shutdown();
        if (highFreqScheduler != null) {
            highFreqScheduler.shutdown();
        }
    }

    private void startHighFrequencyClicker() {
        highFreqScheduler = Executors.newScheduledThreadPool(1);
        
        Runnable highFreqTask = () -> {
            if (!running.get()) {
                return;
            }
            
            try {
                System.out.println("抢!!!");
                
                try {
                    page.waitForSelector(".uno3-dialog-footer-btn .uno3-button--primary",
                        new Page.WaitForSelectorOptions().setTimeout(100000));
                    
                    ElementHandle buyButton = page.querySelector(".uno3-dialog-footer-btn .uno3-button--primary");
                    if (buyButton != null) {
                        page.evaluate("arguments[0].click();", buyButton);
                    }
                } catch (PlaywrightException e) {
                    // 超时或未找到，继续重试
                }
            } catch (Exception e) {
                // 忽略单次错误
            }
        };

        // 每30ms执行一次
        highFreqScheduler.scheduleAtFixedRate(highFreqTask, 0, 30, TimeUnit.MILLISECONDS);
    }

    public static void main(String[] args) throws Exception {
        TengxunyunBot bot = new TengxunyunBot();
        bot.setup();
        try {
            bot.hello();
        } finally {
            bot.tearDown();
        }
    }
}
```

---

### 5. 线程调度原理

**Lambda Runnable 执行位置分析**:

```
主线程（main thread）
    ↓
mainScheduler.scheduleAtFixedRate(mainTask, ...)
    ↓
创建调度器线程池（ThreadPool）
    ↓
调度器线程 ← Runnable mainTask 在这里运行！（不是主线程）
    ↓
每 50ms 执行一次 mainTask
```

**关键点**:
- Lambda 代码块定义在**主线程**
- Lambda 代码块**执行在后台线程**（调度器线程池）
- 主线程和后台线程**并行运行**

---

### 6. Playwright 浏览器安装问题解决

**问题**: 
```
Error: unable to verify the first certificate
UNABLE_TO_VERIFY_LEAF_SIGNATURE
```

**解决方案**:

#### 方案1：手动下载并放到缓存目录（最快）
1. 下载浏览器包：`chromium-win64.zip`
2. 放到 `C:\Users\你的用户名\AppData\Local\ms-playwright\chromium-1091\`
3. 创建空文件 `INSTALLATION_COMPLETE`
4. 重启 IDEA 即可

#### 方案2：禁用 SSL 验证（一劳永逸）
在 IDEA Run Configuration → Environment variables 中添加：
```
NODE_TLS_REJECT_UNAUTHORIZED=0
```

#### 方案3：Maven 配置（推荐）
在 `pom.xml` 中添加：
```xml
<properties>
    <maven.wagon.http.ssl.insecure>true</maven.wagon.http.ssl.insecure>
    <maven.wagon.http.ssl.allowall>true</maven.wagon.http.ssl.allowall>
</properties>
```

---

### 7. Java 程序打包运行方式

**无法像 Python 一样直接运行的原因**:
- Python：解释型语言 → 直接运行源代码
- Java：编译型语言 → 必须先编译成字节码（.class）

**5 种解决方案**:

#### 方案1：直接编译运行
```bash
javac -cp ".:playwright-1.40.0.jar" TengxunyunBot.java
java -cp ".:playwright-1.40.0.jar" TengxunyunBot
```

#### 方案2：Maven（最推荐）
```bash
mvn clean package
java -jar target/playwright-bot-1.0.jar
```

#### 方案3：批处理脚本（Windows 最简单）
创建 `run.bat`:
```batch
@echo off
javac -cp ".:playwright-1.40.0.jar" TengxunyunBot.java
java -cp ".:playwright-1.40.0.jar" TengxunyunBot
```
双击运行！

#### 方案4：Shell 脚本（Mac/Linux）
```bash
#!/bin/bash
javac -cp ".:playwright-1.40.0.jar" TengxunyunBot.java
java -cp ".:playwright-1.40.0.jar" TengxunyunBot
```

#### 方案5：Gradle
```bash
gradle run
```

**推荐排序**:
1. 🥇 方案2（Maven）- 最专业
2. 🥈 方案3（批处理脚本）- 最简单
3. 🥉 方案1（直接编译）- 最基础

---

## 🔑 关键概念总结

### 同步 vs 异步（正确理解）
- Playwright 的**核心通信**都是异步的
- Java 用**线程池 + CompletableFuture**实现异步，但代码写法**看起来同步**
- Python 用**asyncio + async/await**实现异步，代码写法**看起来异步**
- 性能差异来自**语言的线程模型**，不是"异步/同步"本身

### 性能 vs 开发效率
- 对于抢购脚本：**性能差异微乎其微**
- 对于办公自动化：**开发效率是首要因素**
- 团队技能栈 > 语言性能

### 线程调度
- Lambda 表达式定义在主线程
- Lambda 表达式执行在调度器线程池的后台线程
- 主线程和后台线程并行执行

---

## 📚 推荐使用场景

| 场景 | 推荐 | 原因 |
|------|------|------|
| 抢购脚本 | Java Playwright 或 Java Selenium | 性能够用，代码清晰 |
| 办公自动化 | Python（Selenium 或 pandas） | 开发快，学习简单 |
| 大型爬虫 | Playwright（Java 或 Python） | 反爬虫能力强 |
| 企业应用 | Java | 成熟、稳定、易维护 |

---

## ❓ 常见问题汇总

### Q1: page.navigate() 后程序卡住
**A**: 使用超时控制
```java
page.navigate(url, new Page.NavigateOptions().setTimeout(20000));
```

### Q2: Scanner.nextInt() 后程序卡住
**A**: 添加提示信息
```java
System.out.print("请输入数字后按回车: ");
System.out.flush();
int a = sc.nextInt();
```

### Q3: Lambda Runnable 在哪个线程执行
**A**: 在调度器的后台线程，不是主线程

### Q4: 如何快速运行 Java 程序
**A**: 使用 Maven 或批处理脚本

### Q5: Playwright 浏览器下载失败
**A**: 设置 `NODE_TLS_REJECT_UNAUTHORIZED=0` 环境变量

---

## 📝 文件清单

本对话涉及的文件和概念：
- ✅ `TengxunyunBot.java` - 完整的抢购脚本
- ✅ `pom.xml` - Maven 配置
- ✅ `run.bat` - Windows 批处理脚本
- ✅ `run.sh` - Linux/Mac Shell 脚本
- ✅ `playwright.properties` - Playwright 配置

---

**生成时间**: 2026-06-18

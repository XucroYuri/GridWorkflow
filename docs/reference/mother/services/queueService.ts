
import { TaskType, GlobalTaskStatus, TaskPriority, TaskPayload, TaskModule } from '../types';

interface ITaskExecutor {
  execute<T>(task: QueuedTask<T>, signal: AbortSignal): Promise<T>;
}

class LocalExecutor implements ITaskExecutor {
  private readonly TIMEOUTS: Record<TaskType, number> = {
      'ANALYSIS': 900000, 
      'RENDERING': 900000, 
      'REASONING': 300000  
  };

  async execute<T>(task: QueuedTask<T>, signal: AbortSignal): Promise<T> {
    const timeoutDuration = this.TIMEOUTS[task.type] || 300000;
    
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`TASK_TIMEOUT: ${task.label}`));
      }, timeoutDuration);

      const cleanup = () => {
          clearTimeout(timer);
          signal.removeEventListener('abort', onAbort);
      };

      const onAbort = () => {
          cleanup();
          reject(new Error("TASK_ABORTED"));
      };

      if (signal.aborted) return onAbort();
      signal.addEventListener('abort', onAbort);

      Promise.resolve().then(() => task.fn(task.id, signal))
        .then(result => {
          cleanup();
          resolve(result);
        })
        .catch(err => {
          cleanup();
          reject(err);
        });
    });
  }
}

type TaskResolver = (value: any) => void;
type TaskRejecter = (reason?: any) => void;

interface QueuedTask<T = any> extends TaskPayload {
  fn: (taskId: string, signal: AbortSignal) => Promise<T>;
  resolve: TaskResolver;
  reject: TaskRejecter;
  abortController?: AbortController;
  useCustomKey?: boolean; // NEW: Fast Lane Flag
}

class APIDispatcher {
  private queue: QueuedTask[] = [];
  private activeTasksMap = new Map<string, QueuedTask>();
  private executor: ITaskExecutor = new LocalExecutor();
  
  // Lane Limits
  private readonly MAX_SYSTEM_CONCURRENCY = 3;  // Conservative limit for Shared Proxy
  private readonly MAX_USER_CONCURRENCY = 10;   // Higher limit for BYOK (User Keys)
  
  private readonly MODULE_CONCURRENCY: Record<TaskModule, number> = {
    SCRIPT: 1,      
    STORYBOARD: 2,  
    ASSETS: 2,      
    SYSTEM: 2       
  };

  private listeners: ((status: GlobalTaskStatus, userId?: string) => void)[] = [];

  public subscribe(fn: (status: GlobalTaskStatus, userId?: string) => void) {
    this.listeners.push(fn);
    this.notify();
    return () => { this.listeners = this.listeners.filter(l => l !== fn); };
  }

  private notify() {
    const activeList = Array.from(this.activeTasksMap.values());
    const globalStats = {
      activeReasoning: activeList.filter(t => t.type === 'REASONING').length,
      activeRendering: activeList.filter(t => t.type === 'RENDERING').length,
      activeAnalysis: activeList.filter(t => t.type === 'ANALYSIS').length,
      totalQueued: this.queue.length
    };

    this.listeners.forEach(listener => {
      const status: GlobalTaskStatus = {
        globalStats,
        userStats: { ...globalStats, myQueued: this.queue.length }, 
        activeDetails: activeList.map(this.sanitizeTask),
        queuedDetails: this.queue.map(this.sanitizeTask)
      };
      listener(status);
    });
  }

  private sanitizeTask(t: QueuedTask): TaskPayload {
    return {
      id: t.id, ownerId: t.ownerId, type: t.type, module: t.module,
      label: t.label, priority: t.priority, tag: t.tag,
      timestamp: t.timestamp, progress: t.progress, metadata: t.metadata
    };
  }

  public updateTaskProgress(taskId: string, progress: number) {
      const task = this.activeTasksMap.get(taskId);
      if (task) {
          task.progress = progress;
          this.notify();
      }
  }

  public async enqueue<T>(
    ownerId: string, type: TaskType, module: TaskModule, label: string, 
    fn: (taskId: string, signal: AbortSignal) => Promise<T>, 
    priority: TaskPriority = 'LOW', tag?: string, metadata?: Record<string, any>,
    useCustomKey: boolean = false
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const newTask: QueuedTask<T> = { 
        id: crypto.randomUUID(), ownerId, type, module, label, priority, tag, 
        timestamp: Date.now(), progress: 0, metadata, fn, resolve, reject,
        abortController: new AbortController(),
        useCustomKey
      };
      
      if (priority === 'HIGH') this.queue.unshift(newTask);
      else this.queue.push(newTask);
      
      this.process();
      this.notify(); 
    });
  }

  public cancelTask(taskId: string, ownerId: string) {
    const qIdx = this.queue.findIndex(t => t.id === taskId && t.ownerId === ownerId);
    if (qIdx !== -1) {
      this.queue[qIdx].reject(new Error("TASK_CANCELLED_BY_USER"));
      this.queue.splice(qIdx, 1);
    }
    const active = this.activeTasksMap.get(taskId);
    if (active && active.ownerId === ownerId) {
        active.abortController?.abort();
    }
    this.notify();
  }

  public cancelByTag(tag: string, ownerId: string) {
    this.queue = this.queue.filter(t => {
        if (t.tag === tag && t.ownerId === ownerId) {
            t.reject(new Error("TASK_CANCELLED_BY_USER"));
            return false;
        }
        return true;
    });
    this.activeTasksMap.forEach(t => {
        if (t.tag === tag && t.ownerId === ownerId) t.abortController?.abort();
    });
    this.notify();
  }

  public cancelAll(ownerId: string) {
    this.queue = this.queue.filter(t => {
        if (t.ownerId === ownerId) { t.reject(new Error("STOPPED")); return false; }
        return true;
    });
    this.activeTasksMap.forEach(t => {
        if (t.ownerId === ownerId) { t.abortController?.abort(); }
    });
    this.notify();
  }

  public prioritizeTask(taskId: string, ownerId: string) {
    const idx = this.queue.findIndex(t => t.id === taskId && t.ownerId === ownerId);
    if (idx !== -1) {
      const task = this.queue.splice(idx, 1)[0];
      task.priority = 'HIGH';
      this.queue.unshift(task);
      this.notify();
    }
  }

  private async process() {
    if (this.queue.length === 0) return;

    // Separate Active Tasks into Lanes
    const activeTasks = Array.from(this.activeTasksMap.values());
    const systemLaneCount = activeTasks.filter(t => !t.useCustomKey).length;
    const userLaneCount = activeTasks.filter(t => t.useCustomKey).length;

    for (let i = 0; i < this.queue.length; i++) {
      const task = this.queue[i];
      const isUserKey = !!task.useCustomKey;

      // Check Lane Limits
      if (isUserKey) {
          if (userLaneCount >= this.MAX_USER_CONCURRENCY) continue;
      } else {
          if (systemLaneCount >= this.MAX_SYSTEM_CONCURRENCY) continue;
      }

      // Check Module Limits (Optional: loosen this for User Lane if needed)
      const activeInModule = activeTasks.filter(t => t.module === task.module).length;
      if (activeInModule >= (this.MODULE_CONCURRENCY[task.module] || 1) && !isUserKey) {
          // Strict module limits for System Lane, relaxed for User Lane could be implemented here
          continue; 
      }

      // Dispatch
      this.queue.splice(i, 1);
      this.runTask(task);
      
      // Stop loop only if we saturated available slots in current iteration
      if (isUserKey && userLaneCount + 1 >= this.MAX_USER_CONCURRENCY) break;
      if (!isUserKey && systemLaneCount + 1 >= this.MAX_SYSTEM_CONCURRENCY) break;
      
      i--; // Adjust index since we spliced
    }
  }

  private async runTask(task: QueuedTask) {
    this.activeTasksMap.set(task.id, task);
    this.notify();

    try {
      const result = await this.executor.execute(task, task.abortController!.signal);
      task.resolve(result);
    } catch (error: any) {
      if (error.message !== 'TASK_ABORTED' && error.message !== 'TASK_CANCELLED_BY_USER') {
          task.reject(error);
      }
    } finally {
      this.activeTasksMap.delete(task.id);
      this.notify();
      this.process(); 
    }
  }
}

export const apiDispatcher = new APIDispatcher();

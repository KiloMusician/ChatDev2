import React from "react";

export type TaskStatus = "queued" | "running" | "completed" | "failed";

export interface TaskItem {
    id: string;
    status: TaskStatus;
    title?: string;
    updatedAt?: string;
}

export interface TaskQueueDashboardProps {
    title?: string;
    tasks?: TaskItem[];
}

const TaskQueueDashboard: React.FC<TaskQueueDashboardProps> = ({
    title = "Task Queue",
    tasks = [],
}) => {
    return (
        <section className="task-queue-dashboard">
            <header className="task-queue-dashboard__header">
                <h2>{title}</h2>
                <span>{tasks.length} task(s)</span>
            </header>
            {tasks.length === 0 ? (
                <p className="task-queue-dashboard__empty">No tasks in the queue.</p>
            ) : (
                <ul className="task-queue-dashboard__list">
                    {tasks.map((task) => (
                        <li key={task.id} className={`task task--${task.status}`}>
                            <div className="task__title">{task.title ?? task.id}</div>
                            <div className="task__meta">
                                <span className="task__status">{task.status}</span>
                                {task.updatedAt ? (
                                    <time className="task__time">{task.updatedAt}</time>
                                ) : null}
                            </div>
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
};

export default TaskQueueDashboard;
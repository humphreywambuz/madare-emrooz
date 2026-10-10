/**
 * Runs `task` while no other tab of this site is running a task of the same name (Web Locks).
 * Where the browser has no Web Locks it simply runs.
 */
export function exclusive<T>(name: string, task: () => Promise<T>): Promise<T> {
  // The lock API types its result as a nested promise; it resolves to the task's own value.
  return typeof navigator !== 'undefined' && navigator.locks ? (navigator.locks.request(name, task) as Promise<T>) : task()
}

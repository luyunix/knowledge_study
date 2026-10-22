import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

/** One local version's request-admission gate. Not a distributed discovery protocol. */
public final class LeasedVersion {
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition empty = lock.newCondition();
    private boolean accepting = true;
    private int inFlight;

    public final class Lease implements AutoCloseable {
        private boolean released;
        private Lease() { }
        @Override public void close() {
            lock.lock();
            try {
                if (released) return;
                released = true;
                if (--inFlight == 0) empty.signalAll();
            } finally { lock.unlock(); }
        }
    }

    public Lease tryAcquire() {
        lock.lock();
        try {
            if (!accepting) return null;
            inFlight++;
            return new Lease();
        } finally { lock.unlock(); }
    }

    public void beginDrain() {
        lock.lock();
        try { accepting = false; } finally { lock.unlock(); }
    }

    public boolean awaitEmpty(long timeout, TimeUnit unit) throws InterruptedException {
        long remaining = unit.toNanos(timeout);
        lock.lockInterruptibly();
        try {
            if (accepting) throw new IllegalStateException("drain must start first");
            while (inFlight != 0) {
                if (remaining <= 0) return false;
                remaining = empty.awaitNanos(remaining);
            }
            return true;
        } finally { lock.unlock(); }
    }
}

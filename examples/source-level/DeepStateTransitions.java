import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

/** Controlled state transitions; not a test of HotSpot GC or scheduling fairness. */
public final class DeepStateTransitions {
    static final AtomicInteger initCount = new AtomicInteger();
    static final CountDownLatch entered = new CountDownLatch(1);
    static final CountDownLatch allowInit = new CountDownLatch(1);
    static final AtomicReference<Throwable> failure = new AtomicReference<>();

    static final class Slow {
        static final int value = initialize();
        private static int initialize() {
            initCount.incrementAndGet();
            entered.countDown();
            await(allowInit);
            return 42;
        }
    }

    static final class Broken {
        static final int value = initialize();
        private static int initialize() { throw new IllegalStateException("fixture"); }
    }

    static final class Recursive {
        static int first = readSecond();
        static int second = 7;
        static int readSecond() { return second; }
    }

    static void await(CountDownLatch latch) {
        try {
            if (!latch.await(5, TimeUnit.SECONDS)) throw new AssertionError("latch timeout");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new AssertionError(e);
        }
    }

    static Thread start(String name, Runnable body) {
        Thread t = new Thread(() -> {
            try { body.run(); } catch (Throwable e) { failure.compareAndSet(null, e); }
        }, name);
        t.start();
        return t;
    }

    static void join(Thread t) throws InterruptedException {
        t.join(6000);
        if (t.isAlive()) throw new AssertionError("thread timeout: " + t.getName());
        if (failure.get() != null) throw new AssertionError(failure.get());
    }

    static void initialization() throws Exception {
        Class.forName("DeepStateTransitions$Slow", false, DeepStateTransitions.class.getClassLoader());
        if (initCount.get() != 0) throw new AssertionError("load initialized unexpectedly");
        Thread first = start("first", () -> { if (Slow.value != 42) throw new AssertionError(); });
        await(entered);
        CountDownLatch secondStarted = new CountDownLatch(1);
        Thread second = start("second", () -> {
            secondStarted.countDown();
            if (Slow.value != 42) throw new AssertionError();
        });
        await(secondStarted);
        allowInit.countDown();
        join(first); join(second);
        if (initCount.get() != 1) throw new AssertionError("multiple initializers");
        if (Recursive.first != 0 || Recursive.second != 7) throw new AssertionError();
        try { int ignored = Broken.value; throw new AssertionError("expected first failure"); }
        catch (ExceptionInInitializerError expected) {
            if (!(expected.getCause() instanceof IllegalStateException)) throw new AssertionError();
        }
        try { int ignored = Broken.value; throw new AssertionError("expected erroneous state"); }
        catch (NoClassDefFoundError expected) { }
        System.out.println("Class load != initialization; concurrent use initializes once; recursive default and error states verified");
    }

    static void condition() throws Exception {
        ReentrantLock lock = new ReentrantLock();
        Condition ready = lock.newCondition();
        CountDownLatch waiting = new CountDownLatch(1);
        CountDownLatch resumed = new CountDownLatch(1);
        boolean[] predicate = {false};
        Thread waiter = start("condition-waiter", () -> {
            lock.lock(); lock.lock();
            try {
                waiting.countDown();
                while (!predicate[0]) {
                    try { ready.await(); }
                    catch (InterruptedException e) { throw new AssertionError(e); }
                }
                if (!lock.isHeldByCurrentThread() || lock.getHoldCount() != 2) throw new AssertionError();
                resumed.countDown();
            } finally { lock.unlock(); lock.unlock(); }
        });
        await(waiting);
        lock.lock(); // Can only acquire after await fully releases the two holds.
        try {
            predicate[0] = true;
            ready.signal();
            if (resumed.getCount() != 1) throw new AssertionError("signal granted lock ownership");
        } finally { lock.unlock(); }
        await(resumed); join(waiter);
        System.out.println("Condition signal does not transfer ownership; await reacquires the saved hold count");
    }

    public static void main(String[] args) throws Exception {
        System.out.println("Runtime: " + Runtime.version());
        initialization();
        condition();
    }
}

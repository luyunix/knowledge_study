import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/** Deterministic/reference and concurrent invariant tests, not a throughput benchmark. */
public final class CoverageMechanics {
    private static void require(boolean condition) {
        if (!condition) throw new AssertionError();
    }

    private static void lru() throws Exception {
        HandwrittenLru<Integer, Integer> cache = new HandwrittenLru<>(2);
        cache.put(1,10); cache.put(2,20); require(cache.get(1)==10);
        cache.put(3,30); require(cache.get(2)==null);
        cache.put(1,11); require(cache.keysMostRecentFirst().equals(List.of(1,3)));
        cache.checkInvariants();
        HandwrittenLru<Integer,Integer> zero = new HandwrittenLru<>(0);
        zero.put(1,1); require(zero.get(1)==null); zero.checkInvariants();
        try { new HandwrittenLru<>(-1); throw new AssertionError(); }
        catch (IllegalArgumentException expected) { }

        HandwrittenLru<Integer,Integer> target = new HandwrittenLru<>(7);
        List<Integer> recency = new ArrayList<>();
        Map<Integer,Integer> values = new HashMap<>();
        Random random = new Random(20261022);
        for (int i=0;i<100_000;i++) {
            int key = random.nextInt(13);
            if (random.nextBoolean()) {
                int value = random.nextInt(); target.put(key,value);
                recency.remove((Integer)key); recency.add(0,key); values.put(key,value);
                if (recency.size()>7) values.remove(recency.remove(recency.size()-1));
            } else {
                require(java.util.Objects.equals(target.get(key),values.get(key)));
                if (values.containsKey(key)) { recency.remove((Integer)key); recency.add(0,key); }
            }
            require(target.keysMostRecentFirst().equals(recency));
            target.checkInvariants();
        }
        AtomicReference<Throwable> error = new AtomicReference<>();
        CountDownLatch start = new CountDownLatch(1);
        List<Thread> threads = new ArrayList<>();
        for (int t=0;t<8;t++) {
            final int id=t;
            Thread worker=new Thread(()->{
                try {
                    start.await();
                    for(int i=0;i<5000;i++) {
                        target.put((i+id)%13,i); target.get((i*7+id)%13);
                        target.checkInvariants();
                    }
                } catch(Throwable e) { error.compareAndSet(null,e); }
            });
            threads.add(worker);worker.start();
        }
        start.countDown();
        for(Thread t:threads){t.join(15_000);require(!t.isAlive());}
        if(error.get()!=null) throw new AssertionError(error.get());
        System.out.println("Handwritten LRU: 100000 reference steps and 8 concurrent invariant workers passed");
    }

    private static void drain() throws Exception {
        LeasedVersion version = new LeasedVersion();
        LeasedVersion.Lease first=version.tryAcquire();require(first!=null);
        version.beginDrain();require(version.tryAcquire()==null);
        require(!version.awaitEmpty(0,TimeUnit.MILLISECONDS));
        first.close();first.close(); // Duplicate release must not decrement twice.
        require(version.awaitEmpty(1,TimeUnit.SECONDS));
        require(version.tryAcquire()==null);
        System.out.println("Drain: admission stops atomically; existing lease delays disposal; duplicate close is safe");
    }

    private record Segment(long sum,long prefix,long suffix,long best) { }
    private static Segment merge(Segment a, Segment b) {
        return new Segment(a.sum+b.sum,Math.max(a.prefix,a.sum+b.prefix),
                Math.max(b.suffix,b.sum+a.suffix),Math.max(Math.max(a.best,b.best),a.suffix+b.prefix));
    }
    private static Segment divide(int[] a,int lo,int hi) {
        if(hi-lo==1){long x=a[lo];return new Segment(x,x,x,x);}
        int mid=(lo+hi)>>>1;return merge(divide(a,lo,mid),divide(a,mid,hi));
    }
    private static long prefix(int[] a) {
        long sum=0,min=0,best=Long.MIN_VALUE;
        for(int x:a){sum+=x;best=Math.max(best,sum-min);min=Math.min(min,sum);}
        return best;
    }
    private static long brute(int[] a) {
        long best=Long.MIN_VALUE;
        for(int i=0;i<a.length;i++){long sum=0;for(int j=i;j<a.length;j++){sum+=a[j];best=Math.max(best,sum);}}
        return best;
    }
    private static void maxSubarray() {
        int count=0;
        for(int length=1;length<=7;length++) {
            int possibilities=(int)Math.pow(5,length);
            for(int encoded=0;encoded<possibilities;encoded++) {
                int[] a=new int[length];int remaining=encoded;
                for(int i=0;i<length;i++){a[i]=remaining%5-2;remaining/=5;}
                long expected=brute(a);require(prefix(a)==expected);require(divide(a,0,a.length).best==expected);count++;
            }
        }
        int[] overflow={Integer.MAX_VALUE,Integer.MAX_VALUE};
        require(prefix(overflow)==4294967294L);
        System.out.println("Prefix-minimum and segment-merge maximum subarray: "+count+" exhaustive inputs passed");
    }
    public static void main(String[] args) throws Exception { lru();drain();maxSubarray(); }
}

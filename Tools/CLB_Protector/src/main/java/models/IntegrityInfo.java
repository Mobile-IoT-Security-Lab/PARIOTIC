package models;

import java.util.List;

public class IntegrityInfo {
    // {\"origin_func\": \"" + self.function_name + "\", \"new_func\": \"" + new_func_name + "\", \"seed\": " + str(seed) + "}
    private String source_file;
    private String origin_func;
    private String new_func;
    private long seed;
    private String encryption_key;
    private List<Integer[]> tmps;

    public IntegrityInfo(String source_file, String origin_func, String new_func, long seed, String encryption_key, List<Integer[]> tmps) {
        this.source_file = source_file;
        this.origin_func = origin_func;
        this.new_func = new_func;
        this.seed = seed;
        this.encryption_key = encryption_key;
        this.tmps = tmps;
    }

    public String getSource_file() {
        return source_file;
    }

    public String getOrigin_func() {
        return origin_func;
    }

    public String getNew_func() {
        return new_func;
    }

    public long getSeed() {
        return seed;
    }

    public long hashString(byte[] bytes) {
        long mask = (long) Math.pow(2, 32) - 1;

        long h = seed & mask;
        for (int i = 0; i < bytes.length; i++) {
            byte b = bytes[i];
            h = (h + Byte.toUnsignedInt(b)) & mask;
            h = (h + (h << 10) & mask) & mask;
            h = (h ^ ((h >> 6) & mask)) & mask;
        }
        h = (h + ((h << 3) & mask)) & mask;
        h = (h ^ ((h >> 11) & mask)) & mask;
        h = (h + ((h << 15) & mask)) & mask;

        return h;
    }

    public byte[] encryptBodyBytes(byte[] body, int size) {
        byte[] key = encryption_key.getBytes();
        assert key.length >= 1;
        assert size > body.length;
        for (int i = 0; i < size-4; i++) {
            body[i+4] = (byte) (Byte.toUnsignedInt(body[i+4]) ^ Byte.toUnsignedInt((byte)key[i%key.length]));
        }
        return body;
    }

    public Integer[] getTmp(int pos) {
        return tmps.get(pos);
    }

}


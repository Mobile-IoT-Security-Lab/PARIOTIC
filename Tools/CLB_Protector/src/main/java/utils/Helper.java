package utils;

import com.google.gson.Gson;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;

public class Helper {

    public static void reverse(byte[] arr) {
        for(int i = 0; i < arr.length / 2; i++) {
            byte temp = arr[i];
            arr[i] = arr[arr.length - i - 1];
            arr[arr.length - i - 1] = temp;
        }
        // return arr;
    }

    public static String[] getUnsignedBytes(byte[] originalBytes) {
        String[] result = new String[originalBytes.length];
        for (int i = 0; i < originalBytes.length; i++) {
            result[i] = Integer.toHexString(Byte.toUnsignedInt(originalBytes[i]));
        }
        return result;
    }

    public static String getUnsignedBytesString(byte[] originalBytes) {
        StringBuilder result = new StringBuilder();
        for (byte originalByte : originalBytes) {
            result.append(Integer.toHexString(Byte.toUnsignedInt(originalByte)));
            if ((result.length() % 2) != 0)
                result.insert(result.length() - 1, '0');
        }
        return result.toString();
    }

    public static <T> List<T> readFile(String filePath, Class<T> targetClass) throws Exception {
        List<T> result = new ArrayList<>();
        File file = new File(filePath);
        BufferedReader br = new BufferedReader(new FileReader(file));
        String line = null;
        while ((line = br.readLine()) != null) {
            result.add((new Gson()).fromJson(line, targetClass));
        }
        return result;
    }

}

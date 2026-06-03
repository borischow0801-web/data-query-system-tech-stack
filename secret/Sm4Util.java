package com.example.demo;

import cn.hutool.core.util.RandomUtil;
import cn.hutool.crypto.symmetric.SymmetricCrypto;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.util.encoders.Hex;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.security.Security;
import java.util.Base64;

public class Sm4Util {


    public static final String ALGORITHM_NAME_CBC_PADDING = "SM4/CBC/PKCS7Padding";


    /**
     * 用于新秘钥生成
     */
    public static final String ALGORITHM_NAME_ECB_PADDING = "SM4/ECB/PKCS5Padding";


    /**
     * 算法名称
     */
    public static final String ALGORITHM_NAME = "SM4";

     public static String getKey(){
         String sm4Key = RandomUtil.randomString(RandomUtil.BASE_CHAR_NUMBER, 16);
         return sm4Key;
     }

    /**
     * SM4的ECB加密算法
     * @param content   待加密字符串, hex字符串
     * @param key       密钥
     * @return
     */
    public static String EcbEncrypt(String content, String key) {
        //sm4加密业务报文
        SymmetricCrypto sm4 = new SymmetricCrypto("SM4/ECB/PKCS5Padding", key.getBytes());
        String sm4Encrypt = sm4.encryptHex(content);
        return sm4Encrypt;
    }

    /**
     * SM4的ECB加密算法
     * @param content   待加密字符串, hex字符串
     * @param key       密钥
     * @return
     */
    public static String Ecbdecrypt(String content, String key) {
        //sm4加密业务报文
        SymmetricCrypto sm4 = new SymmetricCrypto("SM4/ECB/PKCS5Padding", key.getBytes());
        String sm4Decrypt = sm4.decryptStr(content);
        return sm4Decrypt;
    }

    // cbc加密要加上，否则报错
    static {
        try {
            Security.addProvider(new BouncyCastleProvider());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * SM4加密
     * CBC P5填充解密
     *
     * @param sm4Key 密钥
     * @param data   将要加密数据
     * @return 加密结果
     */
    public static String encryptCbcPadding(String sm4Key, String data) {
        try {
            //密钥
            byte[] appSecretEncData = sm4Encrypt(padRight(sm4Key, 16, "0").getBytes(StandardCharsets.UTF_8), sm4Key.getBytes(StandardCharsets.UTF_8));
            //新秘钥串（将byte转换为16进制）
            byte[] key = Hex.toHexString(appSecretEncData).toUpperCase().substring(0, 16).getBytes(StandardCharsets.UTF_8);
            //偏移量，CBC每轮迭代会和上轮结果进行异或操作，由于首轮没有可进行异或的结果，所以需要设置偏移量，一般用密钥做偏移量
            byte[] iv = padRight(sm4Key, 16, "0").getBytes(StandardCharsets.UTF_8);
            Cipher cipher = generateCbcCipher(ALGORITHM_NAME_CBC_PADDING, Cipher.ENCRYPT_MODE,
                    key, iv);
            byte[] encryptBytes = cipher.doFinal(data.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(encryptBytes);
        } catch (Exception e) {
            e.printStackTrace();
//			log.error(e.getMessage(), e);
        }
        return null;
    }


    /**
     * SM4解密
     * CBC P5填充解密
     *
     * @param sm4Key     密钥
     * @param cipherText 加密数据
     * @return 解密结果
     */
    public static String decryptCbcPadding(String sm4Key, String cipherText) {
        try {
            //密钥
            byte[] appSecretEncData = sm4Encrypt(padRight(sm4Key, 16, "0").getBytes(StandardCharsets.UTF_8), sm4Key.getBytes(StandardCharsets.UTF_8));
            //新秘钥串
            byte[] key = Hex.toHexString(appSecretEncData).toUpperCase().substring(0, 16).getBytes(StandardCharsets.UTF_8);
            //偏移量，CBC每轮迭代会和上轮结果进行异或操作，由于首轮没有可进行异或的结果，所以需要设置偏移量，一般用密钥做偏移量
            byte[] iv = padRight(sm4Key, 16, "0").getBytes(StandardCharsets.UTF_8);
            Cipher cipher = generateCbcCipher(ALGORITHM_NAME_CBC_PADDING, Cipher.DECRYPT_MODE,
                    key, iv);
            byte[] cipherTextByte = Base64.getDecoder().decode(cipherText);
            byte[] decryptBytes = cipher.doFinal(cipherTextByte);
            return new String(decryptBytes, StandardCharsets.UTF_8);
        } catch (Exception e) {
        }
        return null;
    }

    /**
     * SM4加密(用于生成新的秘钥)
     *
     */
    public static byte[] sm4Encrypt(byte[] appIdBytes, byte[] keyBytes) {
        if (appIdBytes.length != 16) {
            throw new RuntimeException("err key length");
        }
        try {
            Key key = new SecretKeySpec(appIdBytes, "SM4");
            Cipher out = Cipher.getInstance(ALGORITHM_NAME_ECB_PADDING, BouncyCastleProvider.PROVIDER_NAME);
            out.init(Cipher.ENCRYPT_MODE, key);
            return out.doFinal(keyBytes);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public static String padRight(String l, int size, String pad) {
        int al = l.length();
        int a = size - al;
        StringBuilder sb = new StringBuilder();
        if (a < 0) {
            return l.substring(0, size);
        } else {
            for (int i = 0; i < a; i++) {
                sb.append(pad);
            }
        }
        return l + sb.toString();
    }

    /**
     * CBC P5填充加解密Cipher初始化
     *
     * @param algorithmName 算法名称
     * @param mode          1 加密 2解密
     * @param key           密钥
     * @param iv            偏移量，CBC每轮迭代会和上轮结果进行异或操作，由于首轮没有可进行异或的结果，
     *                      所以需要设置偏移量，一般用密钥做偏移量
     * @return Cipher
     */
    private static Cipher generateCbcCipher(String algorithmName, int mode, byte[] key, byte[] iv) {
        try {
            Cipher cipher = Cipher.getInstance(algorithmName, BouncyCastleProvider.PROVIDER_NAME);
            Key sm4Key = new SecretKeySpec(key, ALGORITHM_NAME);
            IvParameterSpec ivParameterSpec = new IvParameterSpec(iv);
            cipher.init(mode, sm4Key, ivParameterSpec);
            return cipher;
        } catch (Exception e) {
        }
        return null;
    }

    public static void main(String[] args) throws Exception{
//        String s = "372901195705280238";
//        String key = getKey();
//        System.out.println("密钥："+key);
//        String encrypt = EcbEncrypt(s,key);
//        System.out.println("加密："+encrypt);
//        String decrypt = Ecbdecrypt("f6345c405dc31ebb931eca9c0792f744477fec180199eac6814009c642e29a2b","hbvq1sraf0y487sy");
//        System.out.println("解密："+decrypt);
        System.out.println(encryptCbcPadding("0DF96485EA384BA6","民航专业工程及含有政府投资的民航建设项目初步设计重大变更审批"));
        System.out.println(decryptCbcPadding("0DF96485EA384BA6","ZJN00K8S6ffGh93Rdo9nsQxhHbPVkTjpRfr0ok74+uvv4fbecKqYIIq80ixJqRlfgFwpeIBO23qdw6RHJnjilJqbspiecjCD0cxA2x0BpS1xbU9TJamGOt3sv44hR8WrMgUUV1ZacQMR+HtjhthR3c6lgfYGdZXgYde6QwLekbtQ4W+Oi8nBTmiqta+pdz1nOhLJWbPsBcYky7O1g3iEVOAjeuzEa/0vLKKj4brH318="));
        //        System.out.println(EcbEncrypt(null,"hbvq1sraf0y487sy"));
    }
}

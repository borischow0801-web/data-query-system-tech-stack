package com.example.demo;

import cn.hutool.core.util.CharsetUtil;
import cn.hutool.core.util.HexUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.crypto.BCUtil;
import cn.hutool.crypto.ECKeyUtil;
import cn.hutool.crypto.SecureUtil;
import cn.hutool.crypto.SmUtil;
import cn.hutool.crypto.asymmetric.KeyType;
import cn.hutool.crypto.asymmetric.SM2;
import com.alibaba.fastjson.JSONObject;
import org.bouncycastle.jcajce.provider.asymmetric.ec.BCECPublicKey;
import org.springframework.core.env.Environment;
import org.springframework.util.StringUtils;

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.security.KeyPair;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Random;


public class Sm2Util {
    /**
     * sm2明文加密
     * PRIVATE_KEY:生成的私钥
     * PUBLIC_KEY：生成的公钥
     * @param data 加密前的明文
     * @return 加密后的密文
     */
    public static String encryptData(String data,String PUBLIC_KEY) {
        SM2 sm2 = SmUtil.sm2(null, ECKeyUtil.toSm2PublicParams(PUBLIC_KEY));
        String encryptBcd = sm2.encryptBcd(data, KeyType.PublicKey);
        // 这里的处理前端也可以处理，这个就看怎么约定了，其实都无伤大雅
        if (StrUtil.isNotBlank(encryptBcd)) {
            // 生成的加密密文会带04，因为前端sm-crypto默认的是1-C1C3C2模式，这里需去除04才能正常解密
            if (encryptBcd.startsWith("04")) {
                encryptBcd = encryptBcd.substring(2);
            }
            // 前端解密时只能解纯小写形式的16进制数据，这里需要将所有大写字母转化为小写
            encryptBcd = encryptBcd.toLowerCase();
        }
        return encryptBcd;
    }

    /**
     * sm2密文解密
     * PRIVATE_KEY:生成的私钥
     * PUBLIC_KEY：生成的公钥
     * @param encryptData 加密密文
     * @return 解密后的明文字符串
     */
    public static String decryptData(String encryptData, String PRIVATE_KEY) throws Exception {
        if (StrUtil.isBlank(encryptData)) {
            throw new RuntimeException("解密串为空，解密失败");
        }
        SM2 sm2 = SmUtil.sm2(ECKeyUtil.toSm2PrivateParams(PRIVATE_KEY), null);
        // BC库解密时密文开头必须带04，如果没带04则需补齐
        if (!encryptData.startsWith("04")) {
            encryptData = "04".concat(encryptData);
        }
        byte[] decryptFromBcd = sm2.decryptFromBcd(encryptData, KeyType.PrivateKey);
        if (decryptFromBcd != null && decryptFromBcd.length > 0) {
            return StrUtil.utf8Str(decryptFromBcd);
        } else {
            throw new Exception("密文解密失败");
        }
    }

}


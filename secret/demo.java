package com.example.demo;

import com.alibaba.fastjson.JSONObject;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

public class demo {
    private static final String token = "e55bf2e9302e77fdeb901adce18bf5ba";
    private static final String sm4_secret = Sm4Util.getKey();
    private static final String sm2_publicKey = "04f8116d3137224eda2b1a3485ed6bcf130ef7ccb1ba89e0528bf36552b1983a6808f703c467d978c9ece4b630305a1b9876e5b1c7dd338749e06dda49760de09a";


    public static void main(String[] args) throws Exception {
        String url="http://localhost:9999/gate/api/hcp/getBusinessInfoBySblsh";
        RestTemplate restTemplate = new RestTemplate();

        // sm4 对 参数 进行加密
        String content = "{\"sblsh\":\"03302095117791\"}";
        String encryptStr = Sm4Util.EcbEncrypt(content,sm4_secret);

        // sm2 对 sm4密钥 进行加密
        String secret = Sm2Util.encryptData(sm4_secret,sm2_publicKey);

        // 创建 HTTP 头
        HttpHeaders headers = new HttpHeaders();
        // json格式
        headers.setContentType(MediaType.APPLICATION_JSON);
        // header中设置 token 和 secret
        headers.add("token",token);
        headers.add("secret",secret);

        // 创建请求体
        Map<String, Object> requestBody = new HashMap<>();
        // 放入加密参数
        requestBody.put("data", encryptStr);

        // 创建 HTTP 实体
        HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(requestBody, headers);

        ResponseEntity<String> result = restTemplate.postForEntity(url,requestEntity,String.class);
        if(result.getStatusCodeValue()==200) {
            JSONObject jsonObject = JSONObject.parseObject(result.getBody());
            if(jsonObject.getInteger("code")==200){
                // 获取返回值
                String returnStr = jsonObject.getString("data");
                // sm4 对 返回值 解密
                String decryptStr = Sm4Util.Ecbdecrypt(returnStr,sm4_secret);
                System.out.println(decryptStr);
            }
        }
    }
}


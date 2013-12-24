package org.apache.stratos.cartridge.agent.util;

import org.apache.commons.codec.binary.Base64;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.stratos.cartridge.agent.config.CartridgeAgentConfiguration;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketAddress;
import java.util.ArrayList;
import java.util.List;
import java.util.StringTokenizer;

/**
 * Cartridge agent utility methods.
 */
public class CartridgeAgentUtils {
    private static final Log log = LogFactory.getLog(CartridgeAgentUtils.class);

    public static List<String> splitUsingTokenizer(String string, String delimiter) {
        StringTokenizer tokenizer = new StringTokenizer(string, delimiter);
        List<String> list = new ArrayList<String>(string.length());
        while (tokenizer.hasMoreTokens()) {
            list.add(tokenizer.nextToken());
        }
        return list;
    }

    public static String decryptPassword(String repoUserPassword) {
        String decryptPassword = "";
        String secret = CartridgeAgentConfiguration.getInstance().getCartridgeKey();
        SecretKey key;
        Cipher cipher;
        Base64 coder;
        key = new SecretKeySpec(secret.getBytes(), "AES");
        try {
            cipher = Cipher.getInstance("AES/ECB/PKCS5Padding", "SunJCE");
            coder = new Base64();
            byte[] encrypted = coder.decode(repoUserPassword.getBytes());
            cipher.init(Cipher.DECRYPT_MODE, key);
            byte[] decrypted = cipher.doFinal(encrypted);
            decryptPassword = new String(decrypted);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return decryptPassword;
    }

    public static void waitUntilPortsActive() {
        long portCheckTimeOut = 1000 * 60 * 10;
        String portCheckTimeOutStr = System.getProperty("port.check.timeout");
        if (StringUtils.isNotBlank(portCheckTimeOutStr)) {
            portCheckTimeOut = Integer.parseInt(portCheckTimeOutStr);
        }
        if (log.isDebugEnabled()) {
            log.debug("Port check timeout: " + portCheckTimeOut);
        }

        long startTime = System.currentTimeMillis();
        boolean active = false;
        while (!active) {
            if(log.isInfoEnabled()) {
                log.info("Waiting for ports to be active");
            }
            active = checkPortsActive();
            long endTime = System.currentTimeMillis();
            long duration = endTime - startTime;
            if (duration > portCheckTimeOut) {
                return;
            }
            try {
                Thread.sleep(5000);
            } catch (InterruptedException e) {
            }
        }
    }

    public static boolean checkPortsActive() {
        List<Integer> ports = CartridgeAgentConfiguration.getInstance().getPorts();
        if (ports.size() == 0) {
            throw new RuntimeException("No ports found");
        }
        for (int port : ports) {
            Socket socket = null;
            try {
                SocketAddress httpSockaddr = new InetSocketAddress("localhost", port);
                socket = new Socket();
                socket.connect(httpSockaddr, 5000);
                if (log.isInfoEnabled()) {
                    log.info(String.format("Port %s is active", port));
                }
            } catch (Exception e) {
                if (log.isInfoEnabled()) {
                    log.info(String.format("Port %s is not active", port));
                }
                return false;
            } finally {
                if (socket != null) {
                    try {
                        socket.close();
                    } catch (IOException e) {
                    }
                }
            }
        }
        return true;
    }
}
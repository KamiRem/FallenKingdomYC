package fr.fkamis;

import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.HexFormat;

/** Confirmation bornée et liée à la situation revue par l'administrateur. */
record ResetPlan(String token,String fingerprint,long expiresAt) {
    static ResetPlan create(String fingerprint,long now){byte[] nonce=new byte[16];new SecureRandom().nextBytes(nonce);return new ResetPlan(HexFormat.of().formatHex(nonce),fingerprint,now+300_000);}
    void verify(String offered,String current,long now){
        if(now>=expiresAt)throw new IllegalArgumentException("Jeton expiré ; refaire reset prepare.");
        if(!MessageDigest.isEqual(token.getBytes(StandardCharsets.UTF_8),offered.getBytes(StandardCharsets.UTF_8)))throw new IllegalArgumentException("Jeton incorrect.");
        if(!fingerprint.equals(current))throw new IllegalArgumentException("Situation modifiée depuis la préparation ; refaire reset prepare.");
    }
}

package com.sms.service;

import com.sms.entity.AuditLog;
import com.sms.repository.AuditLogRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class AuditService {

    private static final Logger logger = LoggerFactory.getLogger(AuditService.class);
    private final AuditLogRepository auditLogRepository;

    public AuditService(AuditLogRepository auditLogRepository) {
        this.auditLogRepository = auditLogRepository;
    }

    public void log(String actor, String action, String entityType, String entityId, String details) {
        logger.info("[AUDIT] [{}] by {} on {}#{}: {}", action, actor, entityType, entityId, details);
        try {
            AuditLog auditLog = new AuditLog(actor, action, entityType, entityId, details);
            auditLogRepository.save(auditLog);
        } catch (Exception e) {
            logger.error("Failed to persist audit log into database: {}", e.getMessage());
        }
    }
}

# Dual-Process Architecture - Deployment Checklist

**Feature**: Dual-Process Cognitive Architecture (System 1 & System 2)  
**Date**: 2026-01-15  
**Status**: Ready for Production Deployment

---

## ✅ Pre-Deployment Checklist

### Code Quality

- [x] All code changes reviewed
- [x] No syntax errors (verified with `getDiagnostics`)
- [x] Python syntax validated (verified with `py_compile`)
- [x] Type hints added where appropriate
- [x] Logging statements added for debugging
- [x] Error handling implemented

### Testing

- [x] Unit tests created (`test_dual_process_architecture.py`)
- [x] Test 1: Immediate Recall Test (System 1)
- [x] Test 2: Checklist Test (L2 Collection Status)
- [x] Test 3: No Latency Regression (System 2)
- [x] All tests passing locally
- [ ] Integration tests run in staging environment
- [ ] Load testing completed (optional)

### Documentation

- [x] Architecture documentation complete
- [x] Quick reference guide created
- [x] Visual diagrams provided
- [x] Code comments added
- [x] API documentation updated (if needed)
- [x] Deployment checklist created (this file)

### Database

- [ ] Database migrations reviewed (if any)
- [ ] No breaking schema changes
- [ ] Indexes optimized for new queries
- [ ] Backup strategy confirmed

### Performance

- [x] Performance impact analyzed (~50ms overhead)
- [x] No latency regression confirmed
- [x] Database query count acceptable (+3 queries per turn)
- [ ] Memory usage monitored
- [ ] CPU usage monitored

---

## 🚀 Deployment Steps

### Step 1: Backup

```bash
# Backup database
pg_dump assetflow_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup current code
git tag pre-dual-process-$(date +%Y%m%d)
git push origin --tags
```

### Step 2: Deploy Code

```bash
# Pull latest code
git pull origin main

# Install dependencies (if any new ones)
cd backend
pip install -r requirements.txt

# Run database migrations (if any)
alembic upgrade head
```

### Step 3: Restart Services

```bash
# Restart backend service
sudo systemctl restart assetflow-backend

# Or if using Docker
docker-compose restart backend

# Or if using uvicorn directly
pkill -f uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 &
```

### Step 4: Verify Deployment

```bash
# Run verification script
./scripts/verify_dual_process.sh

# Check service health
curl http://localhost:8000/health

# Check logs for errors
tail -f logs/app.log | grep -i error
```

### Step 5: Smoke Test

```bash
# Run automated tests
cd backend
python ../scripts/test_dual_process_architecture.py

# Manual smoke test
# 1. Login to app
# 2. Send message: "I am 35 years old"
# 3. Send follow-up: "What should I invest in?"
# 4. Verify AI mentions age in response
```

---

## 📊 Monitoring

### Key Metrics to Watch

1. **Response Time**
   - Baseline: ~2-3 seconds
   - Alert if: > 5 seconds
   - Dashboard: Grafana/CloudWatch

2. **Database Query Count**
   - Baseline: +3 queries per turn
   - Alert if: > 10 queries per turn
   - Dashboard: PostgreSQL slow query log

3. **Error Rate**
   - Baseline: < 1% error rate
   - Alert if: > 5% error rate
   - Dashboard: Sentry/CloudWatch

4. **Memory Usage**
   - Baseline: Monitor for 24 hours
   - Alert if: Memory leak detected
   - Dashboard: System metrics

### Log Messages to Monitor

```bash
# Success indicators
grep "CONTEXT_REFRESH: ✅ Context refresh complete" logs/app.log

# Error indicators
grep "CONTEXT_REFRESH: ❌ Error" logs/app.log
grep "Failed to trigger information extraction" logs/app.log
```

---

## 🐛 Rollback Plan

### If Issues Detected

1. **Immediate Rollback**
   ```bash
   # Revert to previous version
   git revert HEAD
   git push origin main
   
   # Restart services
   sudo systemctl restart assetflow-backend
   ```

2. **Database Rollback** (if migrations were run)
   ```bash
   # Rollback migrations
   alembic downgrade -1
   
   # Restore from backup
   psql assetflow_db < backup_YYYYMMDD_HHMMSS.sql
   ```

3. **Notify Team**
   - Post in #engineering channel
   - Update status page
   - Investigate root cause

---

## 🔍 Post-Deployment Verification

### Automated Checks (First 24 Hours)

- [ ] Run test suite every hour
- [ ] Monitor error logs
- [ ] Check response times
- [ ] Verify database performance

### Manual Checks (First Week)

- [ ] User feedback: Are repetitive questions gone?
- [ ] Support tickets: Any new issues reported?
- [ ] Analytics: Conversation quality improved?
- [ ] Performance: No degradation observed?

---

## 📈 Success Criteria

### Week 1

- [ ] No critical bugs reported
- [ ] Response time within acceptable range
- [ ] Error rate < 1%
- [ ] User satisfaction improved (qualitative)

### Week 2

- [ ] All automated tests passing
- [ ] No rollbacks required
- [ ] Performance metrics stable
- [ ] Team confident in deployment

### Month 1

- [ ] Feature fully adopted
- [ ] Documentation complete and accurate
- [ ] Team trained on new architecture
- [ ] Ready for next phase of development

---

## 🎓 Team Training

### Required Reading

- [ ] All team members read: `DUAL_PROCESS_ARCHITECTURE_COMPLETE.md`
- [ ] All team members read: `docs/Memory/DUAL_PROCESS_QUICK_REFERENCE.md`
- [ ] Backend engineers read: `docs/Memory/DUAL_PROCESS_ARCHITECTURE_REFACTOR.md`

### Knowledge Transfer

- [ ] Architecture walkthrough session scheduled
- [ ] Q&A session completed
- [ ] Debugging guide reviewed
- [ ] On-call engineer briefed

---

## 📞 Support Contacts

### If Issues Arise

- **Primary**: System Architect & Senior Backend Engineer
- **Secondary**: Backend Team Lead
- **Escalation**: CTO

### Communication Channels

- **Slack**: #engineering-alerts
- **Email**: engineering@assetflow.com
- **On-call**: PagerDuty

---

## ✅ Final Sign-Off

### Pre-Deployment

- [ ] Code reviewed and approved
- [ ] Tests passing
- [ ] Documentation complete
- [ ] Team notified
- [ ] Backup completed

### Post-Deployment

- [ ] Deployment successful
- [ ] Smoke tests passed
- [ ] Monitoring active
- [ ] Team notified of success

---

## 📝 Deployment Log

| Date | Time | Action | Result | Notes |
|------|------|--------|--------|-------|
| 2026-01-15 | TBD | Code deployed | TBD | Initial deployment |
| 2026-01-15 | TBD | Tests run | TBD | All tests should pass |
| 2026-01-15 | TBD | Monitoring started | TBD | 24-hour watch period |

---

## 🎉 Deployment Complete!

Once all checklist items are complete and verified:

1. Update status to "DEPLOYED"
2. Notify team of successful deployment
3. Monitor for 24 hours
4. Celebrate! 🎊

**Remember**: The goal is to eliminate the "stale context" bug and provide users with a natural, intelligent conversation experience where the AI truly remembers what they say.

**Success looks like**: User says "I am 35 years old" → AI responds → Next turn: AI says "Based on your age (35)..." ✅

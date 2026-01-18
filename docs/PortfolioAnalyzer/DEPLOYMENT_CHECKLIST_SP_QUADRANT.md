# SP Quadrant Integration - Deployment Checklist

## Pre-Deployment Validation

### 1. Run Validation Script
```bash
cd backend
python scripts/validate_sp_quadrant_integration.py
```

**Expected Output:**
- ✅ All extraction tests pass
- ✅ All fact sheet tests pass
- ✅ All recommendation tests pass
- ✅ All portfolio analyzer tests pass

### 2. Check Code Quality
```bash
# No syntax errors
python -m py_compile app/services/information_extraction.py
python -m py_compile app/services/recommendation_service.py
python -m py_compile app/services/chat_agent.py

# No type errors (if using mypy)
mypy app/services/information_extraction.py
mypy app/services/recommendation_service.py
mypy app/services/chat_agent.py
```

### 3. Test with Real Data
```bash
# Run demo script
python scripts/demo_portfolio_analyzer_refactor.py
```

## Deployment Steps

### 1. Backup Current System
```bash
# Backup database
pg_dump assetflow > backup_$(date +%Y%m%d).sql

# Backup code
git commit -am "Pre-SP-Quadrant-integration backup"
git tag pre-sp-quadrant-$(date +%Y%m%d)
```

### 2. Deploy Code Changes
```bash
# Pull latest changes
git pull origin main

# Restart backend service
systemctl restart assetflow-backend
# OR
docker-compose restart backend
```

### 3. Verify Deployment
```bash
# Check service status
systemctl status assetflow-backend

# Check logs for errors
tail -f /var/log/assetflow/backend.log

# Test extraction endpoint
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "我有 50 万国债"}'
```

## Post-Deployment Validation

### 1. Test Extraction
- [ ] Send test message: "我有 50 万国债"
- [ ] Verify extraction includes `subtype: "bond"` and `risk_level: "low"`
- [ ] Check database: `SELECT * FROM user_assets WHERE name = '国债'`
- [ ] Verify `extra_data` contains metadata

### 2. Test Fact Sheet
- [ ] Send message to trigger fact sheet generation
- [ ] Verify fact sheet displays: "类型: 债券 | 风险: 低风险"
- [ ] Check logs for fact sheet generation

### 3. Test Portfolio Analysis
- [ ] Create user with multiple assets
- [ ] Trigger portfolio analysis
- [ ] Verify SP Quadrant distribution is calculated
- [ ] Verify risk warnings use new SP risk types

### 4. Test Recommendations
- [ ] Verify recommendations are generated for SP risk types
- [ ] Check recommendation mapping: `sp_spending_insufficient` → `investment`
- [ ] Verify product recommendations are appropriate

## Monitoring

### Key Metrics to Watch

1. **Extraction Accuracy**
   - Monitor logs for extraction failures
   - Check metadata completeness rate
   - Track subtype/risk_level extraction success

2. **User Experience**
   - Monitor fact sheet generation time
   - Track user feedback on recommendations
   - Check for any error reports

3. **System Performance**
   - Monitor API response times
   - Check database query performance
   - Track memory usage

### Log Monitoring Commands
```bash
# Watch for extraction errors
tail -f /var/log/assetflow/backend.log | grep "extraction"

# Watch for fact sheet generation
tail -f /var/log/assetflow/backend.log | grep "fact_sheet"

# Watch for recommendation errors
tail -f /var/log/assetflow/backend.log | grep "recommendation"
```

## Rollback Plan

### If Issues Occur

1. **Immediate Rollback**
```bash
# Revert to previous version
git checkout pre-sp-quadrant-$(date +%Y%m%d)

# Restart service
systemctl restart assetflow-backend
```

2. **Restore Database** (if needed)
```bash
# Restore from backup
psql assetflow < backup_$(date +%Y%m%d).sql
```

3. **Notify Team**
- Document the issue
- Create incident report
- Plan fix and re-deployment

## Success Criteria

### Must Pass
- [ ] All validation tests pass
- [ ] No errors in logs for 1 hour
- [ ] Extraction accuracy > 90%
- [ ] Fact sheet displays metadata correctly
- [ ] Recommendations are generated successfully

### Should Pass
- [ ] User feedback is positive
- [ ] System performance is stable
- [ ] No increase in error rates
- [ ] Database queries are efficient

## Documentation Updates

### Update User Documentation
- [ ] Add SP Quadrant explanation to user guide
- [ ] Update FAQ with new features
- [ ] Create tutorial for new metadata display

### Update Developer Documentation
- [ ] Update API documentation
- [ ] Add metadata schema to docs
- [ ] Update integration guide

## Communication Plan

### Internal Team
- [ ] Notify team of deployment
- [ ] Share validation results
- [ ] Provide rollback instructions

### Users
- [ ] Announce new features
- [ ] Explain SP Quadrant benefits
- [ ] Provide feedback channel

## Timeline

### Day 1: Pre-Deployment
- Morning: Run validation tests
- Afternoon: Review results, fix any issues
- Evening: Final code review

### Day 2: Deployment
- Morning: Deploy to staging
- Afternoon: Test on staging
- Evening: Deploy to production

### Day 3: Post-Deployment
- Morning: Monitor logs and metrics
- Afternoon: Collect user feedback
- Evening: Review and document

## Contact Information

### On-Call Support
- Backend Team: backend-oncall@assetflow.com
- DevOps Team: devops-oncall@assetflow.com
- Product Team: product@assetflow.com

### Escalation Path
1. Backend Developer
2. Tech Lead
3. Engineering Manager
4. CTO

## Notes

- Keep this checklist updated with actual deployment experience
- Document any issues encountered and solutions
- Share learnings with the team

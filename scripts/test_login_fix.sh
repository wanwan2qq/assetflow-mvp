#!/bin/bash

# 登录修复验证脚本
# 测试后端API和CORS配置

echo "🧪 登录修复验证测试"
echo "===================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
PASSED=0
FAILED=0

# 测试函数
test_endpoint() {
    local name=$1
    local command=$2
    local expected=$3
    
    echo -n "测试: $name ... "
    
    result=$(eval $command 2>&1)
    
    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        echo "  预期: $expected"
        echo "  实际: $result"
        ((FAILED++))
        return 1
    fi
}

echo "1️⃣ 检查后端服务状态"
echo "-------------------"
test_endpoint "后端健康检查" \
    "curl -s http://localhost:8000/health" \
    "healthy"

echo ""
echo "2️⃣ 检查CORS配置"
echo "-------------------"
test_endpoint "CORS预检请求" \
    "curl -s -X OPTIONS http://localhost:8000/api/v1/auth/login/phone -H 'Origin: http://localhost:8080' -H 'Access-Control-Request-Method: POST' -i" \
    "access-control-allow-origin: http://localhost:8080"

echo ""
echo "3️⃣ 测试登录API"
echo "-------------------"
test_endpoint "发送验证码" \
    "curl -s -X POST http://localhost:8000/api/v1/auth/send-sms -H 'Content-Type: application/json' -d '{\"phone\": \"+8613800138000\"}'" \
    "success"

test_endpoint "手机号登录" \
    "curl -s -X POST http://localhost:8000/api/v1/auth/login/phone -H 'Content-Type: application/json' -d '{\"phone\": \"+8613800138000\", \"verification_code\": \"123456\"}'" \
    "access_token"

echo ""
echo "4️⃣ 测试CORS响应头"
echo "-------------------"
test_endpoint "登录请求CORS头" \
    "curl -s -X POST http://localhost:8000/api/v1/auth/login/phone -H 'Origin: http://localhost:8080' -H 'Content-Type: application/json' -d '{\"phone\": \"+8613800138000\", \"verification_code\": \"123456\"}' -i" \
    "access-control-allow-origin: http://localhost:8080"

echo ""
echo "===================="
echo "📊 测试结果汇总"
echo "===================="
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！登录功能正常工作。${NC}"
    exit 0
else
    echo -e "${RED}⚠️  有 $FAILED 个测试失败，请检查配置。${NC}"
    exit 1
fi

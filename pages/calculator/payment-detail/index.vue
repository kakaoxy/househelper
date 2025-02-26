<template>
  <view class="payment-detail">
    <!-- 顶部汇总信息 -->
    <view class="summary-section" v-if="results">
      <!-- 主要信息卡片 -->
      <view class="main-card">
        <view class="card-header">
          <text class="main-label">{{currentType === 'equal' ? '月还款金额' : '首期还款金额'}}</text>
          <button class="share-btn" open-type="share">
            <image src="/static/icons/share.png" class="share-icon"></image>
          </button>
        </view>
        <text class="main-value">{{currentType === 'equal' ? results.equalLoanPayment.monthlyPayment : results.equalPrincipalPayment.firstMonthPayment}}元</text>
        <view class="sub-info">
          <view class="sub-item">
            <text class="sub-label">还款总额</text>
            <text class="sub-value">{{currentType === 'equal' ? results.equalLoanPayment.totalPayment : results.equalPrincipalPayment.totalPayment}}万元</text>
          </view>
          <view class="sub-item">
            <text class="sub-label">总利息</text>
            <text class="sub-value">{{currentType === 'equal' ? results.equalLoanPayment.totalInterest : results.equalPrincipalPayment.totalInterest}}万元</text>
          </view>
          <view class="sub-item">
            <text class="sub-label">贷款总额</text>
            <text class="sub-value">{{loanAmount / 10000}}万元</text>
          </view>
          <view class="sub-item">
            <text class="sub-label">贷款期数</text>
            <text class="sub-value">{{totalMonths}}期</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 还款方式切换 -->
    <view class="type-switch" v-if="results">
      <view 
        class="switch-item" 
        :class="{ active: currentType === 'equal' }"
        @tap="switchType('equal')"
      >等额本息</view>
      <view 
        class="switch-item" 
        :class="{ active: currentType === 'principal' }"
        @tap="switchType('principal')"
      >等额本金</view>
    </view>

    <!-- 还款明细列表 -->
    <view class="detail-list" v-if="results">
      <view class="list-header">
        <text>期数</text>
        <text>月供</text>
        <text>本金</text>
        <text>利息</text>
      </view>
      <scroll-view scroll-y class="list-content">
        <view 
          class="list-item" 
          v-for="(item, index) in currentSchedule" 
          :key="index"
        >
          <text>第{{index + 1}}期</text>
          <text>{{item.payment}}元</text>
          <text>{{item.principal}}元</text>
          <text>{{item.interest}}元</text>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      currentType: 'equal', // equal: 等额本息, principal: 等额本金
      results: null,
      loanAmount: 0,
      totalMonths: 0,
      monthlyRate: 0,
      equalSchedule: [],
      principalSchedule: []
    }
  },
  computed: {
    currentSchedule() {
      return this.currentType === 'equal' ? this.equalSchedule : this.principalSchedule
    }
  },
  onLoad(options) {
    // 接收上一页传递的参数
    if (options.data) {
      const data = JSON.parse(decodeURIComponent(options.data))
      this.results = data.results
      this.loanAmount = data.loanAmount
      this.totalMonths = data.totalMonths
      this.equalSchedule = data.equalSchedule
      this.principalSchedule = data.principalSchedule
    }
  },
  methods: {
    switchType(type) {
      this.currentType = type
    },
    onShareAppMessage() {
      const paymentInfo = this.currentType === 'equal' ? 
        `月供：${this.results.equalLoanPayment.monthlyPayment}元` : 
        `首期还款：${this.results.equalPrincipalPayment.firstMonthPayment}元`;
      
      return {
        title: `房贷还款计划：${paymentInfo}`,
        path: '/pages/calculator/payment-detail/index?data=' + encodeURIComponent(JSON.stringify({
          results: this.results,
          loanAmount: this.loanAmount,
          totalMonths: this.totalMonths,
          equalSchedule: this.equalSchedule,
          principalSchedule: this.principalSchedule
        }))
      }
    },
  }
}
</script>

<style>
.payment-detail {
  min-height: 100vh;
  background-color: #F2F2F7;
  padding: 32rpx;
  display: flex;
  flex-direction: column;
}

.summary-section {
  margin-bottom: 32rpx;
}

.main-card {
  background-color: #FFFFFF;
  border-radius: 16rpx;
  padding: 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.card-header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}

.share-btn {
  position: absolute;
  top: 32rpx;
  right: 32rpx;
  background: transparent;
  padding: 0;
  border: none;
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.share-btn::after {
  border: none;
}

.share-icon {
  width: 40rpx;
  height: 40rpx;
}
.main-label {
  font-size: 28rpx;
  color: #8E8E93;
  margin-bottom: 12rpx;
}

.main-value {
  font-size: 48rpx;
  color: #007AFF;
  font-weight: 600;
  margin-bottom: 32rpx;
}

.sub-info {
  width: 100%;
  display: flex;
  justify-content: space-between;
  border-top: 1rpx solid #E5E5EA;
  padding-top: 24rpx;
}

.sub-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.sub-label {
  font-size: 24rpx;
  color: #8E8E93;
  margin-bottom: 8rpx;
}

.sub-value {
  font-size: 26rpx;
  color: #333333;
  font-weight: 500;
}

.type-switch {
  display: flex;
  background-color: #FFFFFF;
  border-radius: 16rpx;
  padding: 8rpx;
  margin-bottom: 24rpx;
}

.switch-item {
  flex: 1;
  text-align: center;
  padding: 16rpx;
  font-size: 28rpx;
  border-radius: 12rpx;
}

.switch-item.active {
  background-color: #007AFF;
  color: #FFFFFF;
}
.detail-list {
  background-color: #FFFFFF;
  border-radius: 16rpx;
  padding: 24rpx;
  flex: 1;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 320rpx);
  margin-bottom: 96rpx;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  height: 100%;
}

.list-header {
  display: grid;
  grid-template-columns: 0.8fr 1fr 1fr 1fr;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #E5E5EA;
  font-weight: 500;
}

.list-content {
  max-height: 800rpx;
}

.list-item {
  display: grid;
  grid-template-columns: 0.8fr 1fr 1fr 1fr;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #F2F2F7;
  font-size: 24rpx;
}

.list-header text,
.list-item text {
  text-align: center;
}

.list-item text:first-child {
  color: #8E8E93;
}
</style>
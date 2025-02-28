<template>
  <view class="calendar-page">
    <view class="calendar">
      <view class="calendar-header">
        <text class="year-month">{{ currentYear }}年{{ currentMonth + 1 }}月</text>
        <view class="month-switcher">
          <text @click="changeMonth(-1)" class="switcher-btn">上个月</text>
          <text @click="changeMonth(1)" class="switcher-btn">下个月</text>
          <button class="share-btn" open-type="share">
            <image src="/static/icons/share.png" class="share-icon"></image>
          </button>
        </view>
      </view>
      <view class="weekdays">
        <text v-for="day in weekDays" :key="day" class="weekday">{{ day }}</text>
      </view>
      <view class="days">
        <view v-for="(day, index) in calendarDays" :key="index" 
              :class="['day', { 'other-month': day.otherMonth }]">
          <text class="date">{{ day.date }}</text>
          <view class="deals" v-if="day.deals && !day.future">
            <text :class="['new-house', getTrendClass(day.deals.trend)]" v-if="showNewHouse">{{ currentType === 'all' ? day.deals.newHouse + day.deals.secondHand : day.deals.newHouse }}</text>
            <text :class="['second-hand', getTrendClass(day.deals.trend)]" v-if="showSecondHand && currentType !== 'all'">{{ day.deals.secondHand }}</text>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 月度统计信息 -->
    <view class="monthly-stats">
      <view class="stat-item">
        <text>本月新房累计：{{ monthlyStats.newHouse }}套，</text>
        <text :class="['trend', monthlyStats.newHouseTrend > 0 ? 'up' : monthlyStats.newHouseTrend < 0 ? 'down' : 'same']">环比上月同期{{ monthlyStats.newHouseTrend > 0 ? '上涨' : '下降' }}{{ Math.abs(monthlyStats.newHouseTrend) }}%</text>
      </view>
      <view class="stat-item">
        <text>本月二手累计：{{ monthlyStats.secondHand }}套，</text>
        <text :class="['trend', monthlyStats.secondHandTrend > 0 ? 'up' : monthlyStats.secondHandTrend < 0 ? 'down' : 'same']">环比上月同期{{ monthlyStats.secondHandTrend > 0 ? '上涨' : '下降' }}{{ Math.abs(monthlyStats.secondHandTrend) }}%</text>
      </view>
    </view>
    
    <!-- 底部切换按钮 -->
    <view class="type-switcher">
      <view 
        class="type-btn" 
        :class="{ active: currentType === 'all' }"
        @tap="switchType('all')"
      >全部</view>
      <view 
        class="type-btn" 
        :class="{ active: currentType === 'new' }"
        @tap="switchType('new')"
      >新房</view>
      <view 
        class="type-btn" 
        :class="{ active: currentType === 'second' }"
        @tap="switchType('second')"
      >二手房</view>
    </view>
  </view>
</template>

<script>
import { API_CONFIG, request } from '@/api/config.js';

export default {
  data() {
    return {
      weekDays: ['日', '一', '二', '三', '四', '五', '六'],
      currentYear: new Date().getFullYear(),
      currentMonth: new Date().getMonth(),
      calendarDays: [],
      newHouseDeals: [], // 新房成交量数据
      secondHandDeals: [], // 二手房成交量数据
      currentType: 'all', // 当前选中的类型：all/new/second
      monthlyStats: {
        newHouse: 0,
        secondHand: 0,
        newHouseTrend: 0,
        secondHandTrend: 0
      }
    }
  },
  computed: {
    showNewHouse() {
      return this.currentType === 'all' || this.currentType === 'new'
    },
    showSecondHand() {
      return this.currentType === 'all' || this.currentType === 'second'
    }
  },
  created() {
    this.fetchHouseDeals()
  },
  onShareAppMessage() {
    return {
      title: `${this.currentYear}年${this.currentMonth + 1}月房产成交数据`,
      path: '/pages/calendar/index'
    }
  },
  methods: {
    async fetchHouseDeals() {
      try {
        const response = await request({
          endpoint: API_CONFIG.ENDPOINTS.HOUSE_TRANSACTIONS,
          method: 'GET'
        })
        
        if (!response || !response.statusCode) {
          throw new Error('API响应异常：未获取到有效的状态码');
        }

        if (response.statusCode === 200) {
          const data = response.data
          // 将数据转换为按日期排序的数组
          const deals = new Array(60).fill(null)
          
          data.items.forEach(item => {
            const date = new Date(item.transaction_date)
            const startOfYear = new Date(date.getFullYear(), 0, 1)
            const dayIndex = Math.floor((date - startOfYear) / (24 * 60 * 60 * 1000))
            
            if (dayIndex < 60) {
              deals[dayIndex] = {
                newHouse: item.new_house_count,
                secondHand: item.second_hand_count
              }
            }
          })
          
          // 填充数据
          this.newHouseDeals = deals.map(deal => deal ? deal.newHouse : 0)
          this.secondHandDeals = deals.map(deal => deal ? deal.secondHand : 0)
          
          // 计算月度统计数据
          this.calculateMonthlyStats()
          
          // 重新生成日历数据
          this.generateCalendarDays()
        } else if (response.statusCode === 502) {
          console.error('后端服务器错误(502)，请检查服务器是否正常运行');
          uni.showToast({
            title: '服务器暂时不可用，请稍后再试',
            icon: 'none',
            duration: 2000
          });
        } else {
          console.error('API请求失败，状态码:', response.statusCode);
          uni.showToast({
            title: '数据加载失败，请重试',
            icon: 'none',
            duration: 2000
          });
        }
      } catch (error) {
        console.error('获取房产成交数据失败:', error)
        uni.showToast({
          title: '网络连接失败，请检查网络设置',
          icon: 'none',
          duration: 2000
        });
      }
    },
    generateCalendarDays() {
      const firstDay = new Date(this.currentYear, this.currentMonth, 1)
      const lastDay = new Date(this.currentYear, this.currentMonth + 1, 0)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const days = []
      
      // 填充上个月的日期
      const prevMonthDays = firstDay.getDay()
      const prevMonth = new Date(this.currentYear, this.currentMonth, 0)
      for (let i = prevMonthDays - 1; i >= 0; i--) {
        const date = new Date(this.currentYear, this.currentMonth - 1, prevMonth.getDate() - i)
        days.push({
          date: prevMonth.getDate() - i,
          otherMonth: true,
          future: date > today,
          deals: this.generateMockDeals(date)
        })
      }
      
      // 填充当前月的日期
      for (let i = 1; i <= lastDay.getDate(); i++) {
        const date = new Date(this.currentYear, this.currentMonth, i)
        days.push({
          date: i,
          otherMonth: false,
          future: date > today,
          deals: this.generateMockDeals(date)
        })
      }
      
      // 填充下个月的日期
      const remainingDays = 42 - days.length // 保持6行日历
      for (let i = 1; i <= remainingDays; i++) {
        const date = new Date(this.currentYear, this.currentMonth + 1, i)
        days.push({
          date: i,
          otherMonth: true,
          future: date > today,
          deals: null // 下个月不显示数据
        })
      }
      
      this.calendarDays = days
    },
    generateMockDeals(date) {
      if (!date || !this.newHouseDeals.length || !this.secondHandDeals.length) {
        return null;
      }
      
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (date > today) {
        return null;
      }
      
      // 计算从年初开始的天数
      const startOfYear = new Date(date.getFullYear(), 0, 1);
      const dayIndex = Math.floor((date - startOfYear) / (24 * 60 * 60 * 1000));
      
      if (dayIndex >= this.newHouseDeals.length) {
        return null;
      }
      
      const newHouse = this.newHouseDeals[dayIndex];
      const secondHand = this.secondHandDeals[dayIndex];
      
      // 计算趋势 - 与上周同一天对比
      // 一周是7天，所以上周同一天的索引是当前索引减7
      const lastWeekDayIndex = dayIndex - 7;
      let trend = 'same';
      
      if (lastWeekDayIndex >= 0) {
        // 根据当前选择的类型计算趋势
        let currentValue, lastWeekValue;
        
        if (this.currentType === 'all') {
          currentValue = newHouse + secondHand;
          lastWeekValue = this.newHouseDeals[lastWeekDayIndex] + this.secondHandDeals[lastWeekDayIndex];
        } else if (this.currentType === 'new') {
          currentValue = newHouse;
          lastWeekValue = this.newHouseDeals[lastWeekDayIndex];
        } else { // second
          currentValue = secondHand;
          lastWeekValue = this.secondHandDeals[lastWeekDayIndex];
        }
        
        if (currentValue > lastWeekValue) {
          trend = 'up';
        } else if (currentValue < lastWeekValue) {
          trend = 'down';
        }
      }
      
      return {
        newHouse,
        secondHand,
        trend
      }
    },
    changeMonth(delta) {
      const newMonth = this.currentMonth + delta
      if (newMonth < 0) {
        this.currentMonth = 11
        this.currentYear--
      } else if (newMonth > 11) {
        this.currentMonth = 0
        this.currentYear++
      } else {
        this.currentMonth = newMonth
      }
      this.fetchHouseDeals()
    },
    switchType(type) {
      this.currentType = type
      // 切换类型后重新生成日历数据，以更新趋势颜色
      this.generateCalendarDays()
    },
    getTrendClass(trend) {
      switch(trend) {
        case 'up': return 'trend-up';
        case 'down': return 'trend-down';
        default: return 'trend-same';
      }
    },
    generateTestData() {
      // 生成60个随机数据
      this.newHouseDeals = Array.from({length: 60}, () => Math.floor(Math.random() * 1000) + 100);
      this.secondHandDeals = Array.from({length: 60}, () => Math.floor(Math.random() * 1500) + 200);
      this.generateCalendarDays();
    },
    calculateMonthlyStats() {
      const today = new Date()
      const currentMonthStart = new Date(this.currentYear, this.currentMonth, 1)
      const lastMonthStart = new Date(this.currentYear, this.currentMonth - 1, 1)
      
      // 计算当月累计成交量
      let currentMonthNewHouse = 0
      let currentMonthSecondHand = 0
      let lastMonthNewHouse = 0
      let lastMonthSecondHand = 0
      
      const currentMonthDays = Math.min(
        today.getDate(),
        new Date(this.currentYear, this.currentMonth + 1, 0).getDate()
      )
      
      for (let i = 0; i < currentMonthDays; i++) {
        const date = new Date(this.currentYear, this.currentMonth, i + 1)
        const startOfYear = new Date(date.getFullYear(), 0, 1)
        const dayIndex = Math.floor((date - startOfYear) / (24 * 60 * 60 * 1000))
        
        if (dayIndex < this.newHouseDeals.length) {
          currentMonthNewHouse += this.newHouseDeals[dayIndex]
          currentMonthSecondHand += this.secondHandDeals[dayIndex]
        }
        
        // 计算上月同期数据
        const lastMonthDate = new Date(this.currentYear, this.currentMonth - 1, i + 1)
        const lastMonthStartOfYear = new Date(lastMonthDate.getFullYear(), 0, 1)
        const lastMonthDayIndex = Math.floor((lastMonthDate - lastMonthStartOfYear) / (24 * 60 * 60 * 1000))
        
        if (lastMonthDayIndex >= 0 && lastMonthDayIndex < this.newHouseDeals.length) {
          lastMonthNewHouse += this.newHouseDeals[lastMonthDayIndex]
          lastMonthSecondHand += this.secondHandDeals[lastMonthDayIndex]
        }
      }
      
      // 计算环比变化百分比
      const newHouseTrend = lastMonthNewHouse === 0 ? 0 : Math.round((currentMonthNewHouse - lastMonthNewHouse) / lastMonthNewHouse * 100)
      const secondHandTrend = lastMonthSecondHand === 0 ? 0 : Math.round((currentMonthSecondHand - lastMonthSecondHand) / lastMonthSecondHand * 100)
      
      this.monthlyStats = {
        newHouse: currentMonthNewHouse,
        secondHand: currentMonthSecondHand,
        newHouseTrend: newHouseTrend,
        secondHandTrend: secondHandTrend
      }
    },
  }
}
</script>

<style>
.calendar-page {
  padding: 32rpx;
  background-color: #F2F2F7;
  min-height: 100vh;
}

.calendar {
  background-color: #FFFFFF;
  border-radius: 20rpx;
  padding: 32rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32rpx;
}

.year-month {
  font-size: 34rpx;
  font-weight: 600;
  color: #1C1C1E;
  letter-spacing: -0.5rpx;
}

.month-switcher {
  display: flex;
  gap: 16rpx;
  align-items: center;
}

.share-btn {
  background: transparent;
  padding: 0;
  border: none;
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 8rpx;
}

.share-btn::after {
  border: none;
}

.share-icon {
  width: 40rpx;
  height: 40rpx;
}

.switcher-btn {
  font-size: 28rpx;
  color: #007AFF;
  padding: 12rpx 24rpx;
  border-radius: 16rpx;
  background-color: rgba(0, 122, 255, 0.1);
  transition: all 0.2s ease;
}

.switcher-btn:active {
  opacity: 0.7;
  transform: scale(0.98);
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 16rpx;
  border-bottom: 1rpx solid #E5E5EA;
  padding-bottom: 16rpx;
}

.weekday {
  text-align: center;
  font-size: 26rpx;
  color: #8E8E93;
  font-weight: 500;
  padding: 16rpx 0;
}

.days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8rpx;
  width: 100%;
}

.day {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 8rpx;
  text-align: center;
  border: none;
  border-bottom: 1rpx solid #E5E5EA;
  transition: all 0.2s ease;
  box-sizing: border-box;
  width: 100%;
}

.day:active {
  background-color: rgba(0, 0, 0, 0.05);
}

.day.other-month {
  background-color: #F2F2F7;
  opacity: 0.6;
}

.date {
  font-size: 28rpx;
  font-weight: 500;
  color: #1C1C1E;
  margin-bottom: 8rpx;
  display: block;
}

.deals {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  justify-content: center;
  width: 100%;
  align-items: center;
}

.new-house,
.second-hand {
  font-size: 24rpx;
  padding: 4rpx;
  border-radius: 4rpx;
  display: inline-block;
  min-width: 40rpx;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.new-house {
  background-color: rgba(0, 122, 255, 0.1);
}

.second-hand {
  background-color: rgba(255, 149, 0, 0.1);
}

.trend-up {
  background-color: rgba(255, 59, 48, 0.1);
}

.trend-down {
  background-color: rgba(52, 199, 89, 0.1);
}

.trend-same {
  background-color: rgba(0, 122, 255, 0.1);
}

.type-switcher {
  position: fixed;
  bottom: 48rpx;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  background-color: #FFFFFF;
  border-radius: 16rpx;
  padding: 8rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.type-btn {
  padding: 16rpx 48rpx;
  font-size: 28rpx;
  color: #8E8E93;
  border-radius: 12rpx;
  transition: all 0.2s ease;
  white-space: nowrap;
  flex: 1;
  text-align: center;
}

.type-btn.active {
  background-color: #007AFF;
  color: #FFFFFF;
}

.type-btn:active {
  opacity: 0.8;
}

.test-button {
  position: fixed;
  bottom: 160rpx;
  left: 50%;
  transform: translateX(-50%);
  background-color: #34C759;
  color: #FFFFFF;
  padding: 16rpx 32rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
  box-shadow: 0 4rpx 16rpx rgba(52, 199, 89, 0.2);
}

.test-button:active {
  opacity: 0.8;
  transform: translateX(-50%) scale(0.98);
}
.monthly-stats {
  margin-top: 32rpx;
  padding: 32rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.stat-item {
  margin-bottom: 16rpx;
  font-size: 28rpx;
  color: #1C1C1E;
  line-height: 1.5;
}

.stat-item:last-child {
  margin-bottom: 0;
}

.trend {
  font-weight: 500;
}

.trend.up {
  color: #FF3B30;
}

.trend.down {
  color: #34C759;
}

.trend.same {
  color: #8E8E93;
}
</style>
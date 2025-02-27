<template>
  <view class="calendar-page">
    <view class="calendar">
      <view class="calendar-header">
        <text class="year-month">{{ currentYear }}年{{ currentMonth + 1 }}月</text>
        <view class="month-switcher">
          <text @click="changeMonth(-1)" class="switcher-btn">上个月</text>
          <text @click="changeMonth(1)" class="switcher-btn">下个月</text>
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
    <!-- 测试按钮 -->
    <view class="test-button" @tap="generateTestData">生成测试数据</view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      weekDays: ['日', '一', '二', '三', '四', '五', '六'],
      currentYear: new Date().getFullYear(),
      currentMonth: new Date().getMonth(),
      calendarDays: [],
      newHouseDeals: [], // 新房成交量数据
      secondHandDeals: [], // 二手房成交量数据
      currentType: 'all' // 当前选中的类型：all/new/second
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
    this.generateCalendarDays()
  },
  methods: {
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
      
      // 计算趋势
      const prevDayIndex = dayIndex - 1;
      let trend = 'same';
      
      if (prevDayIndex >= 0) {
        const prevTotal = this.newHouseDeals[prevDayIndex] + this.secondHandDeals[prevDayIndex];
        const currentTotal = newHouse + secondHand;
        
        if (currentTotal > prevTotal) {
          trend = 'up';
        } else if (currentTotal < prevTotal) {
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
      this.generateCalendarDays()
    },
    switchType(type) {
      this.currentType = type
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
    }
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
  padding: 16rpx;
  text-align: center;
  border: none;
  border-bottom: 1rpx solid #E5E5EA;
  transition: all 0.2s ease;
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
}

.new-house,
.second-hand {
  font-size: 24rpx;
  padding: 4rpx;
  border-radius: 4rpx;
  display: inline-block;
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
</style>
<template>
	<view class="calculator">
		<!-- 贷款类型选择 -->
		<view class="section">
			<view class="section-title">贷款类型</view>
			<view class="type-group">
				<view v-for="(type, index) in loanTypes" :key="index"
					:class="['type-item', { active: currentType === type.value }]" @tap="selectType(type.value)">
					{{ type.label }}
				</view>
			</view>
		</view>

		<!-- 基础信息输入 -->
		<view class="section">
			<view class="input-item">
				<text>房屋总价</text>
				<input type="digit" v-model="totalPrice" placeholder="请输入房屋总价" class="input" />
				<text class="unit">万元</text>
			</view>

			<view class="input-item">
				<text>首付</text>
				<view class="down-payment-group">
					<view class="down-payment-ratio">
						<picker :range="downPaymentRatios" @change="onDownPaymentChange" class="picker"
							:disabled="!!downPaymentAmount">
							<view :class="{'disabled-text': !!downPaymentAmount}">
								{{ currentDownPaymentRatio }}%
							</view>
						</picker>
					</view>
					<text class="separator">或</text>
					<view class="down-payment-input">
						<input type="digit" v-model="downPaymentAmount" placeholder="输入首付金额" class="input"
							@input="onDownPaymentAmountChange" />
						<text class="unit">万元</text>
					</view>
				</view>
			</view>

			<view class="input-item">
				<text>按揭年限</text>
				<picker :range="loanYears" @change="onYearChange" class="picker">
					<view>{{ loanYears[selectedYear] }}年</view>
				</picker>
			</view>

			<!-- 商业贷款利率 -->
			<block v-if="currentType !== 'gjj'">
				<view class="input-item">
					<text>商贷利率</text>
					<input type="digit" v-model="commercialRate" placeholder="请输入商贷利率" class="input" />
					<text class="unit">%</text>
				</view>
			</block>

			<!-- 公积金贷款利率 -->
			<block v-if="currentType !== 'commercial'">
				<view class="input-item">
					<text>公积金利率</text>
					<input type="digit" v-model="gjjRate" placeholder="请输入公积金利率" class="input" />
					<text class="unit">%</text>
				</view>
			</block>

			<!-- 组合贷款时的贷款金额分配 -->
			<block v-if="currentType === 'mix'">
				<view class="input-item">
					<text>商贷金额</text>
					<input type="digit" v-model="commercialAmount" placeholder="请输入商贷金额" class="input" />
					<text class="unit">万元</text>
				</view>
			</block>
		</view>

		<!-- 计算按钮 -->
		<button class="calculate-btn" @tap="calculate">开始计算</button>

	</view>
</template>

<script>
	export default {
		data() {
			return {
				loanTypes: [{
						label: '商业贷款',
						value: 'commercial'
					},
					{
						label: '公积金贷款',
						value: 'gjj'
					},
					{
						label: '组合贷款',
						value: 'mix'
					}
				],
				currentType: 'commercial',
				totalPrice: '',
				downPaymentRatios: ['30%', '35%', '40%', '45%', '50%', '55%', '60%', '65%', '70%'],
				selectedDownPayment: 0,
				loanYears: [10, 15, 20, 25, 30],
				selectedYear: 4,
				commercialRate: '3.6',
				gjjRate: '2.85',
				commercialAmount: '',
				showResult: false,
				results: {
					equalLoanPayment: {
						monthlyPayment: 0,
						totalPayment: 0,
						totalInterest: 0
					},
					equalPrincipalPayment: {
						firstMonthPayment: 0,
						monthlyDecrease: 0,
						totalPayment: 0
					}
				},
				downPaymentAmount: '', // 新增：首付金额
				paymentSchedule: [], // 新增：还款计划
				downPaymentRatios: ['15', '20', '25', '30', '35', '40', '45', '50', '55', '60', '65',
					'70'
				], // 修改：默认值从15%开始
				selectedDownPayment: 0, // 默认选择15%
			}
		},
		computed: {
			currentDownPaymentRatio() {
				if (this.downPaymentAmount) {
					return ((this.downPaymentAmount / this.totalPrice) * 100).toFixed(2)
				}
				return this.downPaymentRatios[this.selectedDownPayment]
			}
		},
		methods: {
			selectType(type) {
				this.currentType = type
				this.showResult = false
			},
			onDownPaymentChange(e) {
				this.selectedDownPayment = e.detail.value
				this.showResult = false
			},
			onYearChange(e) {
				this.selectedYear = e.detail.value
				this.showResult = false
			},
			calculate() {
				

				// 验证输入
				if (!this.totalPrice) {
					uni.showToast({
						title: '请输入房屋总价',
						icon: 'none'
					})
					return
				}

				// 计算贷款金额
				const downPaymentRate = this.downPaymentAmount ?
					(this.downPaymentAmount / this.totalPrice) :
					(parseFloat(this.downPaymentRatios[this.selectedDownPayment]) / 100)


				const totalLoan = this.totalPrice * (1 - downPaymentRate)


				const months = this.loanYears[this.selectedYear] * 12


				let monthlyRate, loanAmount

				if (this.currentType === 'commercial') {
					monthlyRate = this.commercialRate / 12 / 100
					loanAmount = totalLoan
					
				} else if (this.currentType === 'gjj') {
					monthlyRate = this.gjjRate / 12 / 100
					loanAmount = totalLoan
					
				} else {
					// 组合贷款的计算逻辑
					
					const commercialMonthlyRate = this.commercialRate / 12 / 100
					const gjjMonthlyRate = this.gjjRate / 12 / 100
					const commercialLoan = parseFloat(this.commercialAmount)
					const gjjLoan = totalLoan - commercialLoan

					

					// 分别计算商贷和公积金的月供
					this.calculateBothMethods(commercialLoan, commercialMonthlyRate, months)
					this.calculateBothMethods(gjjLoan, gjjMonthlyRate, months)
					return
				}

				

				this.calculateBothMethods(loanAmount, monthlyRate, months)
				this.showResult = true
			},
			calculateBothMethods(principal, monthlyRate, months) {
				

				// 计算等额本息还款计划
				const schedule = []
				let remainingPrincipal = principal * 10000
				
				// 计算等额本息的月供
				const monthlyPayment = (principal * 10000 * monthlyRate * Math.pow(1 + monthlyRate, months)) / (Math.pow(1 + monthlyRate, months) - 1)
				
				for (let i = 0; i < months; i++) {
					const interest = remainingPrincipal * monthlyRate
					const principalPayment = monthlyPayment - interest
					remainingPrincipal -= principalPayment

					schedule.push({
						payment: monthlyPayment.toFixed(2),
						principal: principalPayment.toFixed(2),
						interest: interest.toFixed(2)
					})
				}

				this.paymentSchedule = schedule

				// 计算汇总数据
				const totalPayment = monthlyPayment * months / 10000
				const totalInterest = totalPayment - principal

				// 等额本金计算
				const principalSchedule = []
				let remainingPrincipal2 = principal * 10000
				const monthlyPrincipal = principal * 10000 / months

				for (let i = 0; i < months; i++) {
					const interest = remainingPrincipal2 * monthlyRate
					const payment = monthlyPrincipal + interest
					remainingPrincipal2 -= monthlyPrincipal

					principalSchedule.push({
						payment: payment.toFixed(2),
						principal: monthlyPrincipal.toFixed(2),
						interest: interest.toFixed(2)
					})
				}

				// 计算等额本金的汇总数据
      const firstMonthPayment = monthlyPrincipal + principal * 10000 * monthlyRate
      const monthlyDecrease = monthlyPrincipal * monthlyRate
      const totalPayment2 = (firstMonthPayment + (firstMonthPayment - monthlyDecrease * (months - 1))) * months / 2 / 10000
      const totalInterest2 = totalPayment2 - principal

      // 设置计算结果
      this.results = {
        equalLoanPayment: {
          monthlyPayment: monthlyPayment.toFixed(2),
          totalPayment: totalPayment.toFixed(2),
          totalInterest: totalInterest.toFixed(2)
        },
        equalPrincipalPayment: {
          firstMonthPayment: firstMonthPayment.toFixed(2),
          monthlyDecrease: monthlyDecrease.toFixed(2),
          totalPayment: totalPayment2.toFixed(2),
          totalInterest: totalInterest2.toFixed(2)
        }
      }

				// 跳转到还款明细页面
				const navigationData = {
					results: this.results,
					loanAmount: principal * 10000,
					totalMonths: months,
					monthlyRate: monthlyRate,
					equalSchedule: schedule,
					principalSchedule: principalSchedule
				}

				uni.navigateTo({
					url: `/pages/calculator/payment-detail/index?data=${encodeURIComponent(JSON.stringify(navigationData))}`
				})
			}
		}
	}
</script>

<style>
	.calculator {
		padding: 32rpx;
		background-color: #F2F2F7;
		min-height: 100vh;
	}

	.section {
		background-color: #FFFFFF;
		border-radius: 16rpx;
		padding: 24rpx;
		margin-bottom: 24rpx;
	}

	.section-title {
		font-size: 32rpx;
		font-weight: 600;
		margin-bottom: 16rpx;
	}

	.type-group {
		display: flex;
		gap: 16rpx;
	}

	.type-item {
		flex: 1;
		text-align: center;
		padding: 16rpx;
		background-color: #F2F2F7;
		border-radius: 12rpx;
		font-size: 28rpx;
	}

	.type-item.active {
		background-color: #007AFF;
		color: #FFFFFF;
	}
.input-item {
	display: flex;
	align-items: center;
	padding: 24rpx 0;
	border-bottom: 1rpx solid #E5E5EA;
}
.input-item:last-child {
	border-bottom: none;
}
.input-item text {
	width: 160rpx;
	font-size: 28rpx;
}
.input,
.picker {
	flex: 1;
	font-size: 28rpx;
	margin: 0 16rpx;
}
.unit {
	width: 80rpx !important;
	color: #8E8E93;
	text-align: right;
}
.disabled-text {
	color: #999;
}
.down-payment-group {
	flex: 1;
	display: flex;
	align-items: center;
	margin: 0 16rpx;
	gap: 10rpx;
}
.down-payment-input, .down-payment-ratio {
    display: flex;
    align-items: center;
}
.down-payment-input {
    flex: 0.8;
}
.down-payment-ratio {
    flex: 0.2;
}
.separator {
    padding: 0 5rpx;
    color: #8E8E93;
    font-size: 24rpx;
    text-align: center;
}
.unit {
    width: 80rpx !important;
    color: #8E8E93;
    text-align: right;
}
.payment-details {
	margin-top: 16rpx;
}
.payment-header {
	display: grid;
	grid-template-columns: 0.8fr 1fr 1fr 1fr;
	padding: 16rpx 0;
	border-bottom: 1rpx solid #E5E5EA;
	font-weight: 500;
}
.payment-list {
	max-height: 400rpx;
}
.payment-item {
	display: grid;
	grid-template-columns: 0.8fr 1fr 1fr 1fr;
	padding: 16rpx 0;
	border-bottom: 1rpx solid #F2F2F7;
	font-size: 24rpx;
}
.payment-header text,
.payment-item text {
	text-align: center;
}
.payment-item text:first-child {
	color: #8E8E93;
}
</style>
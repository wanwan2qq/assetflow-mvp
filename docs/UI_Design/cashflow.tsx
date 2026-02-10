import React, { useState } from 'react';
import { useNavigation } from '../contexts/NavigationContext';
import { useWealth } from '../contexts/WealthContext';
import { ChevronLeft, Search, ChevronDown, Plus, Repeat, Zap, ArrowRight } from 'lucide-react';
import { BarChart, Bar, ResponsiveContainer, Tooltip, XAxis, Cell } from 'recharts';
import TransactionEditSheet from '../components/TransactionEditSheet';

// Helper to format money
const formatCurrency = (val: number, currency: string) => {
    return new Intl.NumberFormat('zh-CN', { style: 'currency', currency, maximumFractionDigits: 0 }).format(val);
};

const CashFlowPage: React.FC = () => {
    const { goBack } = useNavigation();
    const { transactions, userProfile, addTransaction } = useWealth();
    const [periodMode, setPeriodMode] = useState<'monthly' | 'yearly'>('monthly');
    const [viewMode, setViewMode] = useState<'INCOME' | 'EXPENSE'>('EXPENSE');
    const [isEditSheetOpen, setIsEditSheetOpen] = useState(false);

    // 1. Data Filtering (Current Month)
    const now = new Date();
    const currentMonthTrans = transactions.filter(t => {
        const d = new Date(t.date);
        return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
    });

    // 2. Structural Analysis Calculations
    // Income Structure
    const incomeRecurring = currentMonthTrans.filter(t => t.type === 'income' && t.isRecurring).reduce((s, t) => s + t.amount, 0);
    const incomeOneTime = currentMonthTrans.filter(t => t.type === 'income' && !t.isRecurring).reduce((s, t) => s + t.amount, 0);
    const totalIncome = incomeRecurring + incomeOneTime;

    // Expense Structure
    const expenseRecurring = currentMonthTrans.filter(t => t.type === 'expense' && t.isRecurring).reduce((s, t) => s + t.amount, 0);
    const expenseOneTime = currentMonthTrans.filter(t => t.type === 'expense' && !t.isRecurring).reduce((s, t) => s + t.amount, 0);
    const totalExpense = expenseRecurring + expenseOneTime;

    const netFlow = totalIncome - totalExpense;

    // 3. Chart Data (Stacked)
    const chartData = [
        {
            name: '收入',
            recurring: incomeRecurring,
            onetime: incomeOneTime,
            total: totalIncome
        },
        {
            name: '支出',
            recurring: expenseRecurring,
            onetime: expenseOneTime,
            total: totalExpense
        }
    ];

    const currentDateDisplay = `${now.getFullYear()}年 ${now.getMonth() + 1}月`;

    // 4. List Grouping for the active view
    const activeTransactions = currentMonthTrans.filter(t =>
        viewMode === 'INCOME' ? t.type === 'income' : t.type === 'expense'
    );

    const recurringList = activeTransactions.filter(t => t.isRecurring);
    const oneTimeList = activeTransactions.filter(t => !t.isRecurring);

    // Sort by amount descending for emphasis
    recurringList.sort((a, b) => b.amount - a.amount);
    oneTimeList.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

    const handleSaveTransaction = (data: any) => {
        addTransaction({
            id: Date.now().toString(),
            date: data.date?.toISOString() || new Date().toISOString(),
            amount: data.amount,
            type: data.type,
            category: data.category,
            isRecurring: data.isRecurring,
            description: data.isRecurring ? '周期性项目' : '一次性项目'
        });
    };

    return (
        <div className="h-full overflow-y-auto pb-24 bg-slate-50 flex flex-col">

            {/* 1. Header & Filter (Sticky) */}
            <div className="bg-white sticky top-0 z-20 shadow-sm">
                <div className="px-4 py-3 border-b border-slate-100 flex justify-between items-center">
                    <button onClick={goBack} className="flex items-center text-slate-600">
                        <ChevronLeft size={24} />
                        <span className="text-sm font-medium ml-1">返回</span>
                    </button>
                    <h1 className="text-lg font-bold text-slate-800">现金流结构</h1>
                    <button className="text-slate-600">
                        <Search size={20} />
                    </button>
                </div>

                {/* Date Filter Bar */}
                <div className="px-4 py-2 bg-slate-50/50 backdrop-blur-sm border-b border-slate-200 flex justify-between items-center">
                    <button className="flex items-center space-x-1 text-slate-800 font-bold">
                        <ChevronLeft size={16} className="text-slate-400" />
                        <span>{currentDateDisplay}</span>
                        <ChevronLeft size={16} className="text-slate-400 rotate-180" />
                    </button>
                    <div className="flex bg-slate-200 p-0.5 rounded-lg text-[10px] font-medium">
                        <button
                            onClick={() => setPeriodMode('monthly')}
                            className={`px-3 py-1 rounded-md transition-all ${periodMode === 'monthly' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}
                        >
                            按月
                        </button>
                        <button
                            onClick={() => setPeriodMode('yearly')}
                            className={`px-3 py-1 rounded-md transition-all ${periodMode === 'yearly' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}
                        >
                            按年
                        </button>
                    </div>
                </div>
            </div>

            {/* 2. Summary Card */}
            <div className="px-4 pt-4">
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100">
                    <p className="text-xs text-slate-400 font-medium mb-1">本月净现金流 (Net Cash Flow)</p>
                    <div className="flex items-baseline space-x-2">
                        <span className={`text-3xl font-bold ${netFlow >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                            {netFlow > 0 ? '+' : ''}{formatCurrency(netFlow, userProfile.currency)}
                        </span>
                    </div>
                    <div className="flex space-x-4 mt-2 text-xs text-slate-500">
                        <span>总收入: {formatCurrency(totalIncome, userProfile.currency)}</span>
                        <span>总支出: {formatCurrency(totalExpense, userProfile.currency)}</span>
                    </div>
                </div>
            </div>

            {/* 3. Structured Chart (Core) */}
            <div className="px-4 py-6">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 px-1">收支结构对比</h3>
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 h-64 relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} barCategoryGap="30%">
                            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} dy={10} />
                            <Tooltip
                                cursor={{ fill: '#f1f5f9' }}
                                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                            />
                            {/* Stacked Bars: Bottom is Recurring (Base), Top is One-time (Var) */}
                            <Bar dataKey="recurring" stackId="a" name="固定/周期性" radius={[0, 0, 4, 4]}>
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-rec-${index}`} fill={index === 0 ? '#059669' : '#e11d48'} /> // Emerald-600 vs Rose-600
                                ))}
                            </Bar>
                            <Bar dataKey="onetime" stackId="a" name="变动/一次性" radius={[4, 4, 0, 0]}>
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-one-${index}`} fill={index === 0 ? '#6ee7b7' : '#fda4af'} /> // Emerald-300 vs Rose-300
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>

                    {/* Legend */}
                    <div className="absolute top-4 right-4 flex flex-col space-y-2 text-[10px] text-slate-400 items-end">
                        <div className="flex items-center space-x-1.5">
                            <div className="w-2.5 h-2.5 rounded-sm bg-slate-300/50"></div>
                            <span>变动 (Variable)</span>
                        </div>
                        <div className="flex items-center space-x-1.5">
                            <div className="w-2.5 h-2.5 rounded-sm bg-slate-600"></div>
                            <span>固定 (Fixed)</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* 4. Structure Details Tabs (Sticky) */}
            <div className="sticky top-[105px] z-10 bg-slate-50/95 backdrop-blur px-4 pb-2 border-b border-slate-200/50">
                <div className="flex bg-white rounded-xl p-1 shadow-sm border border-slate-100">
                    <button
                        onClick={() => setViewMode('INCOME')}
                        className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all flex items-center justify-center space-x-2 ${viewMode === 'INCOME' ? 'bg-emerald-50 text-emerald-700 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`}
                    >
                        <div className={`w-2 h-2 rounded-full ${viewMode === 'INCOME' ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                        <span>收入结构</span>
                    </button>
                    <button
                        onClick={() => setViewMode('EXPENSE')}
                        className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all flex items-center justify-center space-x-2 ${viewMode === 'EXPENSE' ? 'bg-rose-50 text-rose-700 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`}
                    >
                        <div className={`w-2 h-2 rounded-full ${viewMode === 'EXPENSE' ? 'bg-rose-500' : 'bg-slate-300'}`} />
                        <span>支出结构</span>
                    </button>
                </div>
            </div>

            {/* 5. Grouped List Content */}
            <div className="px-4 py-4 space-y-8">
                {/* Section A: Recurring (The Base) */}
                <div>
                    <div className="flex justify-between items-end mb-3 px-1">
                        <div className="flex items-center space-x-2">
                            <Repeat size={16} className={viewMode === 'INCOME' ? 'text-emerald-600' : 'text-rose-600'} />
                            <h3 className="text-sm font-bold text-slate-700">固定/周期性 (Recurring)</h3>
                        </div>
                        <span className="text-xs font-semibold text-slate-500">
                            ¥{viewMode === 'INCOME' ? incomeRecurring.toLocaleString() : expenseRecurring.toLocaleString()}
                        </span>
                    </div>

                    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden divide-y divide-slate-50">
                        {recurringList.length > 0 ? recurringList.map(t => (
                            <div key={t.id} className="p-4 flex justify-between items-center group active:bg-slate-50">
                                <div className="flex items-center space-x-3">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${viewMode === 'INCOME' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
                                        {viewMode === 'INCOME' ? <Zap size={18} /> : <Repeat size={18} />}
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-slate-800">{t.category}</p>
                                        <p className="text-xs text-slate-400 flex items-center mt-0.5">
                                            <span className="bg-slate-100 px-1 rounded text-[10px] mr-1">每月</span>
                                            {t.description || '自动入账'}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <span className="font-bold text-slate-800 text-sm">¥{t.amount.toLocaleString()}</span>
                                    <ArrowRight size={14} className="text-slate-300 group-hover:text-slate-500 transition-colors" />
                                </div>
                            </div>
                        )) : (
                            <div className="p-6 text-center text-slate-400 text-xs">本月暂无固定项记录</div>
                        )}
                    </div>
                    <p className="text-[10px] text-slate-400 mt-2 px-2 text-center">
                        💡 点击条目可调整周期规则
                    </p>
                </div>

                {/* Section B: One-time (The Shocks) */}
                <div>
                    <div className="flex justify-between items-end mb-3 px-1">
                        <div className="flex items-center space-x-2">
                            <Zap size={16} className={viewMode === 'INCOME' ? 'text-emerald-400' : 'text-rose-400'} />
                            <h3 className="text-sm font-bold text-slate-700">变动/一次性 (Variable)</h3>
                        </div>
                        <span className="text-xs font-semibold text-slate-500">
                            ¥{viewMode === 'INCOME' ? incomeOneTime.toLocaleString() : expenseOneTime.toLocaleString()}
                        </span>
                    </div>

                    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden divide-y divide-slate-50">
                        {oneTimeList.length > 0 ? oneTimeList.map(t => (
                            <div key={t.id} className="p-4 flex justify-between items-center active:bg-slate-50">
                                <div className="flex items-center space-x-3">
                                    <div className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center text-slate-400">
                                        <Zap size={18} />
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-slate-700">{t.category}</p>
                                        <p className="text-xs text-slate-400 mt-0.5">
                                            {new Date(t.date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })} • {t.description}
                                        </p>
                                    </div>
                                </div>
                                <span className="font-medium text-slate-600 text-sm">¥{t.amount.toLocaleString()}</span>
                            </div>
                        )) : (
                            <div className="p-6 text-center text-slate-400 text-xs">本月暂无一次性变动</div>
                        )}
                    </div>
                </div>
            </div>

            {/* FAB */}
            <button
                onClick={() => setIsEditSheetOpen(true)}
                className={`fixed bottom-8 right-6 w-14 h-14 text-white rounded-full shadow-lg flex items-center justify-center active:scale-95 transition-transform z-50 ${viewMode === 'INCOME' ? 'bg-emerald-600 shadow-emerald-600/30' : 'bg-rose-600 shadow-rose-600/30'}`}
            >
                <Plus size={28} />
            </button>

            <TransactionEditSheet
                isOpen={isEditSheetOpen}
                onClose={() => setIsEditSheetOpen(false)}
                onSave={handleSaveTransaction}
            />
        </div>
    );
};

export default CashFlowPage;
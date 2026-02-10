
import React, { useState, useMemo } from 'react';
import { useWealth } from '../contexts/WealthContext';
import { useNavigation } from '../contexts/NavigationContext';
import { AssetType, Asset } from '../types';
import TransactionEditSheet from '../components/TransactionEditSheet';
import AssetEditSheet from '../components/AssetEditSheet';
import AddMenuSheet from '../components/AddMenuSheet';
import {
    Eye,
    EyeOff,
    TrendingUp,
    TrendingDown,
    CreditCard,
    Home,
    Landmark,
    Shield,
    PieChart,
    Plus,
    Bell,
    MoreHorizontal,
    Building2,
    AlertCircle // Added Import
} from 'lucide-react';

// --- Helpers ---
const formatMoney = (amount: number, currency: string, privacy: boolean, maximumFractionDigits = 0) => {
    if (privacy) return '****';
    return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: currency, maximumFractionDigits }).format(amount);
};

const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
};

// --- Components ---

// 1. Sticky Header
const StickyHeader: React.FC<{ onAddAsset: () => void }> = ({ onAddAsset }) => {
    const { userProfile, togglePrivacyMode } = useWealth();

    return (
        <div className="sticky top-0 z-50 bg-slate-50/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200/60 dark:border-slate-800/60 px-4 py-3 flex justify-between items-center transition-all">
            <div className="flex items-center space-x-2">
                <h1 className="text-lg font-bold text-slate-800 dark:text-slate-100">财富</h1>
            </div>
            <div className="flex items-center space-x-3">
                <button onClick={togglePrivacyMode} className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-colors">
                    {userProfile.privacyMode ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
                <button className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-colors">
                    <Bell size={20} />
                </button>
            </div>
        </div>
    );
};

// 2. Overview Section
const OverviewSection: React.FC = () => {
    const { getNetWorth, userProfile, transactions } = useWealth();
    const netWorth = getNetWorth();

    // Mock Yearly Growth Calculation
    const currentYear = new Date().getFullYear();
    const yearlyIncome = transactions
        .filter(t => new Date(t.date).getFullYear() === currentYear && t.type === 'income')
        .reduce((sum, t) => sum + t.amount, 0);
    const yearlyExpense = transactions
        .filter(t => new Date(t.date).getFullYear() === currentYear && t.type === 'expense')
        .reduce((sum, t) => sum + t.amount, 0);
    const growth = yearlyIncome - yearlyExpense;
    const growthPercent = 12.5; // Mock

    return (
        <div className="px-4 py-4">
            <div className="bg-slate-900 dark:bg-slate-800 rounded-[2rem] p-6 text-white shadow-xl shadow-slate-200 dark:shadow-slate-950 relative overflow-hidden transition-colors">
                {/* Abstract Background Curves */}
                <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-gradient-to-br from-indigo-500/30 to-purple-500/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none"></div>
                <div className="absolute bottom-0 left-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl -ml-10 -mb-10 pointer-events-none"></div>

                {/* Sparkline SVG Mock */}
                <svg className="absolute bottom-0 left-0 w-full h-24 opacity-20 pointer-events-none" preserveAspectRatio="none" viewBox="0 0 100 100">
                    <path d="M0,80 C20,70 40,90 60,60 S80,20 100,40 V100 H0 Z" fill="url(#grad1)" />
                    <defs>
                        <linearGradient id="grad1" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="white" stopOpacity="0.5" />
                            <stop offset="100%" stopColor="white" stopOpacity="0" />
                        </linearGradient>
                    </defs>
                </svg>

                <div className="relative z-10">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-slate-300 text-xs font-medium uppercase tracking-wider mb-1">总净资产 (Net Worth)</p>
                            <h2 className="text-3xl font-bold tracking-tight">
                                {formatMoney(netWorth, userProfile.currency, userProfile.privacyMode)}
                            </h2>
                        </div>
                        {/* Health Score Badge */}
                        <div className="bg-white/10 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/5 flex flex-col items-center">
                            <span className="text-[10px] text-slate-300">健康分</span>
                            <span className="text-lg font-bold text-white">{userProfile.healthScore || '-'}</span>
                        </div>
                    </div>

                    <div className="mt-8 flex items-center justify-between">
                        <div className="flex flex-col">
                            <span className="text-slate-400 text-xs mb-1">年度净增长预测</span>
                            <div className="flex items-center space-x-2">
                                <span className="font-semibold text-lg">{formatMoney(growth, userProfile.currency, userProfile.privacyMode)}</span>
                                <div className="flex items-center text-emerald-400 text-xs font-medium bg-emerald-400/10 px-1.5 py-0.5 rounded">
                                    <TrendingUp size={12} className="mr-0.5" />
                                    +{growthPercent}%
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// 3. Cash Flow Teaser (Redesigned)
const CashFlowTeaser: React.FC = () => {
    const { userProfile } = useWealth();
    const { push } = useNavigation();

    // Calculate current month's flow from transactions
    const { transactions } = useWealth();
    const now = new Date();
    const currentMonthTrans = transactions.filter(t => {
        const d = new Date(t.date);
        return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
    });

    const income = currentMonthTrans.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0);
    const expense = currentMonthTrans.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0);
    const balance = income - expense;

    // Calculate visualization width
    const total = income + expense;
    const incomeWidth = total > 0 ? (income / total) * 100 : 50;

    return (
        <div className="px-4 mb-2">
            <div
                className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05)] border border-slate-100 dark:border-slate-800 cursor-pointer active:scale-[0.99] transition-transform"
                onClick={() => push({ name: 'CASH_FLOW_DETAILS' })}
            >
                <div className="flex justify-between items-center mb-3">
                    <h3 className="font-bold text-slate-800 dark:text-slate-100 text-sm">本月收支概览</h3>
                    <div className="flex items-center space-x-1 text-slate-400 dark:text-slate-500">
                        <span className="text-xs">详情</span>
                        <MoreHorizontal size={14} />
                    </div>
                </div>

                <div className="flex justify-between text-sm mb-3 font-medium">
                    <span className="text-emerald-600 dark:text-emerald-400">+{formatMoney(income, userProfile.currency, userProfile.privacyMode, 0)}</span>
                    <span className="text-rose-500 dark:text-rose-400">-{formatMoney(expense, userProfile.currency, userProfile.privacyMode, 0)}</span>
                </div>

                {/* Bar */}
                <div className="w-full h-2.5 bg-rose-100 dark:bg-rose-900/30 rounded-full overflow-hidden flex mb-3">
                    <div
                        className="h-full bg-emerald-500 rounded-r-sm"
                        style={{ width: `${incomeWidth}%` }}
                    />
                </div>

                <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400 dark:text-slate-500">结余</span>
                    <span className="font-bold text-slate-800 dark:text-slate-100 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md">
                        {balance > 0 ? '+' : ''}{formatMoney(balance, userProfile.currency, userProfile.privacyMode)}
                    </span>
                </div>
            </div>
        </div>
    );
};

// 4. Sticky Tabs
const CATEGORIES = [
    { id: 'ALL', label: '🔴 全部' },
    { id: AssetType.REAL_ESTATE, label: '🏠 房产' },
    { id: AssetType.LIABILITY, label: '💳 负债' },
    { id: 'INVESTMENT', label: '📈 投资' }, // Stock + Fund
    { id: AssetType.INSURANCE, label: '🛡️ 保险' },
    { id: AssetType.BANK_DEPOSIT, label: '💰 现金' },
];

const StickyTabs: React.FC<{ activeTab: string, onTabChange: (id: string) => void }> = ({ activeTab, onTabChange }) => {
    return (
        <div className="sticky top-[56px] z-40 bg-slate-50/95 dark:bg-slate-900/95 backdrop-blur-sm py-2 px-4 border-b border-slate-200/50 dark:border-slate-800/50 -mx-0">
            <div className="flex space-x-2 overflow-x-auto no-scrollbar">
                {CATEGORIES.map(cat => (
                    <button
                        key={cat.id}
                        onClick={() => onTabChange(cat.id)}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${activeTab === cat.id
                                ? 'bg-slate-800 dark:bg-indigo-600 text-white shadow-md'
                                : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 shadow-sm'
                            }`}
                    >
                        {cat.label}
                    </button>
                ))}
            </div>
        </div>
    );
};

// 5. Polymorphic Asset Card Factory
const AssetCardFactory: React.FC<{ asset: Asset }> = ({ asset }) => {
    const { userProfile } = useWealth();
    const { push } = useNavigation();
    const { currency, privacyMode } = userProfile;

    const handleCardClick = () => {
        push({ name: 'ASSET_DETAIL', assetId: asset.id });
    };

    // Common Header
    const CardHeader = ({ icon: Icon, colorClass, darkColorClass }: { icon: any, colorClass: string, darkColorClass?: string }) => (
        <div className="flex justify-between items-start mb-3">
            <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${colorClass} ${darkColorClass || ''}`}>
                    <Icon size={18} />
                </div>
                <div>
                    <h3 className="font-bold text-slate-800 dark:text-slate-100 text-sm leading-tight">{asset.name}</h3>
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium tracking-wide mt-0.5">{asset.type}</p>
                </div>
            </div>
            <button className="text-slate-300 dark:text-slate-600 hover:text-slate-50 p-1">
                <MoreHorizontal size={16} />
            </button>
        </div>
    );

    // --- A. Real Estate Card ---
    if (asset.type === AssetType.REAL_ESTATE) {
        const isPositive = true; // Mock trend
        return (
            <div onClick={handleCardClick} className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05)] border border-slate-100 dark:border-slate-800 mb-3 active:scale-[0.99] transition-transform duration-200 cursor-pointer">
                <CardHeader icon={Home} colorClass="bg-indigo-50 text-indigo-600" darkColorClass="dark:bg-indigo-900/30 dark:text-indigo-400" />

                <div className="flex items-baseline space-x-2 mb-4">
                    <span className="text-2xl font-bold text-slate-800 dark:text-slate-100 tracking-tight">
                        {formatMoney(asset.value, currency, privacyMode)}
                    </span>
                    <div className={`flex items-center text-xs font-bold ${isPositive ? 'text-rose-500 dark:text-rose-400' : 'text-emerald-500 dark:text-emerald-400'}`}>
                        {isPositive ? <TrendingUp size={12} className="mr-0.5" /> : <TrendingDown size={12} className="mr-0.5" />}
                        <span>+2.5%</span>
                    </div>
                </div>

                <div className="border-t border-slate-50 dark:border-slate-800 pt-3 flex justify-between text-xs text-slate-500 dark:text-slate-400">
                    <span>单价: {formatMoney(asset.details?.unitPrice || 0, currency, privacyMode)}/m²</span>
                    <span>2024.02.15 更新</span>
                </div>
            </div>
        );
    }

    // --- B. Liability Card ---
    if (asset.type === AssetType.LIABILITY) {
        // Calculate progress: 1 - (current / original)
        const current = asset.value;
        const original = asset.details?.originalLoanAmount || current * 1.2;
        const progress = Math.min(Math.max(1 - (current / original), 0), 1);
        const percent = Math.round(progress * 100);

        return (
            <div onClick={handleCardClick} className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05)] border border-slate-100 dark:border-slate-800 mb-3 cursor-pointer active:scale-[0.99] transition-transform">
                <CardHeader icon={CreditCard} colorClass="bg-rose-50 text-rose-500" darkColorClass="dark:bg-rose-900/30 dark:text-rose-400" />

                <div className="flex justify-between items-end mb-2">
                    <div>
                        <p className="text-xs text-slate-400 dark:text-slate-500 font-medium mb-0.5">待还本金</p>
                        <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{formatMoney(asset.value, currency, privacyMode)}</p>
                    </div>
                    <div className="text-right">
                        <p className="text-xs text-slate-400 dark:text-slate-500 font-medium mb-0.5">利率</p>
                        <p className="text-sm font-bold text-slate-700 dark:text-slate-300">{asset.details?.interestRate}%</p>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="relative pt-2 pb-4">
                    <div className="flex justify-between text-[10px] text-slate-400 dark:text-slate-500 mb-1">
                        <span>进度 {percent}%</span>
                        <span>剩余 ¥{formatMoney(current, currency, false, 0).replace(/[^\d]/g, '')}</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                        <div className="bg-gradient-to-r from-rose-400 to-rose-600 h-2 rounded-full" style={{ width: `${percent}%` }}></div>
                    </div>
                </div>

                <div className="border-t border-slate-50 dark:border-slate-800 pt-3 flex justify-between text-xs items-center">
                    <span className="text-slate-500 dark:text-slate-400">📅 下次还款: {formatDate(asset.details?.nextPaymentDate)}</span>
                    <span className="font-bold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/30 px-2 py-1 rounded">
                        ¥{formatMoney(asset.details?.nextPaymentAmount || 0, currency, privacyMode, 0).replace(/[^\d,.]/g, '')}
                    </span>
                </div>
            </div>
        );
    }

    // --- C. Investment Card ---
    if (asset.type === AssetType.STOCK || asset.type === AssetType.FUND) {
        const pnl = asset.value - (asset.details?.costBasis || 0);
        const isPositive = pnl >= 0;

        // Chinese Logic: Red for Profit, Green for Loss
        const pnlColorClass = isPositive
            ? 'bg-rose-50 text-rose-500 dark:bg-rose-900/30 dark:text-rose-400'
            : 'bg-emerald-50 text-emerald-500 dark:bg-emerald-900/30 dark:text-emerald-400';

        return (
            <div onClick={handleCardClick} className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05)] border border-slate-100 dark:border-slate-800 mb-3 cursor-pointer active:scale-[0.99] transition-transform">
                <CardHeader icon={PieChart} colorClass="bg-blue-50 text-blue-600" darkColorClass="dark:bg-blue-900/30 dark:text-blue-400" />

                <div className="flex justify-between items-end mb-3">
                    <div>
                        <p className="text-xs text-slate-400 dark:text-slate-500 font-medium mb-0.5">市值 (Market Value)</p>
                        <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{formatMoney(asset.value, currency, privacyMode)}</p>
                    </div>
                    <div className="text-right">
                        <span className={`text-sm font-bold px-2 py-1 rounded ${pnlColorClass}`}>
                            {isPositive ? '+' : ''}{formatMoney(pnl, currency, privacyMode, 0).replace(/[+-]/g, '')}
                        </span>
                    </div>
                </div>

                <div className="flex items-center space-x-2 mb-4">
                    {asset.details?.riskLevel && (
                        <span className={`text-[10px] px-2 py-0.5 rounded border font-medium ${asset.details.riskLevel === 'R4' || asset.details.riskLevel === 'R5'
                                ? 'bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800'
                                : 'bg-slate-50 text-slate-600 border-slate-100 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700'
                            }`}>
                            {asset.details.riskLevel} 中高风险
                        </span>
                    )}
                    <span className="text-[10px] text-slate-400 dark:text-slate-500 border border-slate-100 dark:border-slate-800 px-2 py-0.5 rounded">
                        长期持有
                    </span>
                </div>

                <div className="border-t border-slate-50 dark:border-slate-800 pt-3 text-xs text-slate-400 dark:text-slate-500">
                    持仓成本: {formatMoney(asset.details?.costBasis || 0, currency, privacyMode)}
                </div>
            </div>
        );
    }

    // --- D. Insurance Card (Updated) ---
    if (asset.type === AssetType.INSURANCE) {
        let warningText = null;
        let daysLeft = -1;

        if (asset.details?.renewalDate) {
            const today = new Date();
            const renewal = new Date(asset.details.renewalDate);
            const diffTime = renewal.getTime() - today.getTime();
            daysLeft = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            // Show warning if within 30 days
            if (daysLeft >= 0 && daysLeft <= 30) {
                warningText = `距离续费还有 ${daysLeft} 天`;
            }
        }

        const premiumStr = asset.details?.yearlyPremium
            ? `¥${asset.details.yearlyPremium.toLocaleString()} / 年`
            : '-';

        const dateStr = asset.details?.renewalDate
            ? `(${new Date(asset.details.renewalDate).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })})`
            : '';

        return (
            <div onClick={handleCardClick} className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05)] border border-slate-100 dark:border-slate-800 mb-3 cursor-pointer active:scale-[0.99] transition-transform">
                {/* Header */}
                <CardHeader icon={Shield} colorClass="bg-indigo-50 text-indigo-600" darkColorClass="dark:bg-indigo-900/30 dark:text-indigo-400" />

                {/* Info Grid */}
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <p className="text-xs text-slate-400 dark:text-slate-500 font-medium mb-1">保额</p>
                        <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{formatMoney(asset.details?.coverageAmount || 0, currency, privacyMode)}</p>
                    </div>
                    <div className="text-right">
                        <p className="text-xs text-slate-400 dark:text-slate-500 font-medium mb-1">被保人</p>
                        <p className="text-sm font-bold text-slate-700 dark:text-slate-200">{asset.details?.insuredPerson || '-'}</p>
                    </div>
                </div>

                {/* Warning Bar */}
                {warningText && (
                    <div className="flex items-center space-x-2 text-amber-600 dark:text-amber-500 bg-amber-50 dark:bg-amber-900/20 px-3 py-2 rounded-lg mb-4 text-xs font-bold">
                        <AlertCircle size={14} />
                        <span>{warningText}</span>
                    </div>
                )}

                {/* Footer */}
                <div className="border-t border-slate-50 dark:border-slate-800 pt-3 text-xs text-slate-500 dark:text-slate-400 font-medium">
                    保费: {premiumStr} {dateStr}
                </div>
            </div>
        );
    }

    // --- E. Bank/Cash Card (Updated) ---
    if (asset.type === AssetType.BANK_DEPOSIT) {
        return (
            <div onClick={handleCardClick} className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05)] border border-slate-100 dark:border-slate-800 mb-3 cursor-pointer active:scale-[0.99] transition-transform">
                {/* Header */}
                <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-lg bg-teal-50 text-teal-600 dark:bg-teal-900/30 dark:text-teal-400`}>
                            <Landmark size={18} />
                        </div>
                        <div>
                            <div className="flex items-center space-x-2">
                                <h3 className="font-bold text-slate-800 dark:text-slate-100 text-sm">{asset.name}</h3>
                                {asset.details?.bankName && asset.details.bankName !== asset.name && (
                                    <span className="text-xs text-slate-400">({asset.details.bankName})</span>
                                )}
                            </div>
                        </div>
                    </div>
                    <button className="text-slate-300 dark:text-slate-600 hover:text-slate-50 p-1">
                        <MoreHorizontal size={16} />
                    </button>
                </div>

                {/* Main Content */}
                <div className="flex justify-between items-end">
                    <span className="text-2xl font-bold text-slate-800 dark:text-slate-100 tracking-tight">
                        {formatMoney(asset.value, currency, privacyMode)}
                    </span>

                    <span className="text-xs font-medium text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-800 px-2 py-1 rounded border border-slate-100 dark:border-slate-700">
                        类型: {asset.details?.accountType || '活期'}
                    </span>
                </div>
            </div>
        );
    }

    // Fallback for any other type
    return (
        <div onClick={handleCardClick} className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-800 mb-3">
            <p>Unknown Asset Type</p>
        </div>
    );
};

const WealthPage: React.FC = () => {
    const { assets, addTransaction, addAsset } = useWealth();
    const { push } = useNavigation();
    const [activeTab, setActiveTab] = useState('ALL');
    const [isTxSheetOpen, setIsTxSheetOpen] = useState(false);
    const [isAssetSheetOpen, setIsAssetSheetOpen] = useState(false);
    const [isAddMenuOpen, setIsAddMenuOpen] = useState(false);
    const [selectedAssetType, setSelectedAssetType] = useState<AssetType | null>(null);

    const filteredAssets = useMemo(() => {
        if (activeTab === 'ALL') return assets;
        if (activeTab === 'INVESTMENT') {
            return assets.filter(a => a.type === AssetType.STOCK || a.type === AssetType.FUND);
        }
        return assets.filter(a => a.type === activeTab);
    }, [assets, activeTab]);

    const handleSaveTransaction = (data: any) => {
        // data comes from TransactionEditSheet { type, mode, amount, category, date }
        addTransaction({
            id: Date.now().toString(),
            date: data.date?.toISOString() || new Date().toISOString(),
            amount: data.amount,
            type: data.type,
            category: data.category,
            isRecurring: data.mode === 'recurring',
            description: '手动记录'
        });
    };

    const handleSaveAsset = (asset: Asset) => {
        addAsset(asset);
        // Auto navigate to detail page after creation as per spec
        push({ name: 'ASSET_DETAIL', assetId: asset.id });
    };

    const openAddAsset = (type: AssetType) => {
        setSelectedAssetType(type);
        setIsAddMenuOpen(false);
        setIsAssetSheetOpen(true);
    };

    return (
        <div className="h-full overflow-y-auto pb-24 bg-slate-50 dark:bg-slate-950 transition-colors duration-300">
            <StickyHeader onAddAsset={() => setIsAddMenuOpen(true)} />
            <OverviewSection />
            <CashFlowTeaser />
            <StickyTabs activeTab={activeTab} onTabChange={setActiveTab} />

            <div className="px-4 py-4 min-h-[400px]">
                {filteredAssets.length > 0 ? (
                    filteredAssets.map(asset => (
                        <AssetCardFactory key={asset.id} asset={asset} />
                    ))
                ) : (
                    <div className="flex flex-col items-center justify-center py-16 text-slate-400 dark:text-slate-600">
                        <Building2 size={48} className="mb-4 opacity-10 dark:opacity-20" />
                        <p className="text-sm font-medium opacity-60">暂无该分类资产</p>
                    </div>
                )}

                {/* List Bottom Add Button */}
                <button
                    onClick={() => setIsAddMenuOpen(true)}
                    className="w-full py-4 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl text-slate-400 dark:text-slate-500 text-sm font-medium hover:border-indigo-200 dark:hover:border-indigo-800 hover:text-indigo-400 dark:hover:text-indigo-400 transition-colors flex items-center justify-center space-x-2"
                >
                    <Plus size={18} />
                    <span>手动添加资产</span>
                </button>
            </div>

            {/* Floating Action Button (FAB) for Add Menu */}
            <button
                onClick={() => setIsAddMenuOpen(true)}
                className="fixed bottom-24 right-6 w-14 h-14 bg-indigo-600 text-white rounded-full shadow-lg shadow-indigo-600/30 flex items-center justify-center active:scale-95 transition-transform z-50"
            >
                <Plus size={28} />
            </button>

            {/* 1. Add Menu Sheet */}
            <AddMenuSheet
                isOpen={isAddMenuOpen}
                onClose={() => setIsAddMenuOpen(false)}
                onRecordTransaction={() => {
                    setIsAddMenuOpen(false);
                    setIsTxSheetOpen(true);
                }}
                onAddAsset={openAddAsset}
            />

            {/* 2. Transaction Sheet */}
            <TransactionEditSheet
                isOpen={isTxSheetOpen}
                onClose={() => setIsTxSheetOpen(false)}
                onSave={handleSaveTransaction}
            />

            {/* 3. Asset Sheet (Minimal Creation Form) */}
            <AssetEditSheet
                isOpen={isAssetSheetOpen}
                onClose={() => setIsAssetSheetOpen(false)}
                onSave={handleSaveAsset}
                initialType={selectedAssetType}
            />
        </div>
    );
};

export default WealthPage;

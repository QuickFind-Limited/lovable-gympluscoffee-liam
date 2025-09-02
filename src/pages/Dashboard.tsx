import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, ClipboardList, Check, Bell, Package } from 'lucide-react';
import PurchaseOrderGenerationTransition from '@/components/PurchaseOrderGenerationTransition';
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import Header from '@/components/dashboard/Header';
import AppSidebar from '@/components/dashboard/AppSidebar';
import SearchBar from '@/components/dashboard/SearchBar';
import ChatInterface from '@/components/dashboard/ChatInterface';
import KpiCard from '@/components/dashboard/analytics/KpiCard';
import PurchaseOrderPDFView from '@/components/PurchaseOrderPDFView';
import { useFinancialData } from '@/contexts/FinancialDataContext';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useOpenAISearch } from '@/hooks/useOpenAISearch';
import type { OrderSummaryData } from '@/types/search.types';
interface DashboardProps {
  onNavigateToOrderSummary: (query: string) => void;
}
const Dashboard = ({
  onNavigateToOrderSummary
}: DashboardProps) => {
  const [currentUser, setCurrentUser] = useState<{
    name: string;
    email: string;
  } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoadingOrderSummary, setIsLoadingOrderSummary] = useState(false);
  const [showChatInterface, setShowChatInterface] = useState(false);
  const [showOrderGeneration, setShowOrderGeneration] = useState(false);
  const [chatLoadingMessage, setChatLoadingMessage] = useState('');
  const [isGeneratingPO, setIsGeneratingPO] = useState(false);
  const [showPurchaseOrder, setShowPurchaseOrder] = useState(false);
  const [selectedOrderData, setSelectedOrderData] = useState<{
    supplier: string;
    products: any[];
    totalEstimatedCost: string;
    urgency: string;
    action: string;
  } | null>(null);
  const navigate = useNavigate();
  const {
    toast
  } = useToast();
  const {
    monthlySpendData
  } = useFinancialData();
  useEffect(() => {
    // "Dashboard useEffect running");
    const checkUser = async () => {
      const {
        data: {
          user
        }
      } = await supabase.auth.getUser();
      if (!user) {
        // "No user found, redirecting to auth");
        navigate('/auth');
        return;
      }
      // "User found, setting current user");
      setCurrentUser({
        name: user.email?.split('@')[0] || 'User',
        email: user.email || ''
      });
    };
    checkUser();
  }, [navigate]);
  const handleLogout = async () => {
    try {
      const {
        error
      } = await supabase.auth.signOut();
      if (error) {
        toast({
          title: "Error",
          description: "Failed to sign out",
          variant: "destructive"
        });
        return;
      }
      navigate('/auth');
    } catch (err) {
      toast({
        title: "Error",
        description: "An unexpected error occurred",
        variant: "destructive"
      });
    }
  };
  const handleSupplierClick = () => {
    navigate('/suppliers');
  };
  const handleInventoryClick = () => {
    navigate('/inventory');
  };
  const handleOrdersClick = () => {
    navigate('/orders');
  };
  const handleDashboardClick = () => {
    navigate('/analytics-dashboard');
  };
  const handleDataSourcesClick = () => {
    navigate('/data-sources');
  };
  const handleQuickActionClick = (action: string, orderData?: any) => {
    // "Quick action clicked:", action, orderData);
    if (orderData) {
      // Navigate to purchase order editor with the order data
      const orderDataToPass = orderData.products && orderData.supplier ? orderData : {
        supplier: orderData.supplier,
        products: [{
          title: orderData.title,
          description: orderData.description || '',
          quantity: orderData.quantity,
          estimatedCost: orderData.estimatedCost,
          icon: <Package className="h-4 w-4" />
        }],
        totalEstimatedCost: orderData.estimatedCost,
        urgency: orderData.urgency,
        action: `Generate PO for ${orderData.title} from ${orderData.supplier}`
      };

      // Store order data in sessionStorage to pass to editor
      // 'Dashboard - Storing in sessionStorage:', orderDataToPass);

      // ⚠️ DEBUG: Verify exact data being stored
      // '🚨 DEBUG: Dashboard - EXACT data being stored in sessionStorage:');
      // '🚨 orderDataToPass.products:', JSON.stringify(orderDataToPass.products, null, 2));

      sessionStorage.setItem('purchaseOrderData', JSON.stringify(orderDataToPass));

      // Show generating transition then navigate
      setIsGeneratingPO(true);
    } else {
      // Fall back to search query for legacy actions
      setSearchQuery(action);
    }
  };
  const handlePOGenerationComplete = () => {
    setIsGeneratingPO(false);
    navigate('/purchase-order-editor');
  };
  const handleChatSubmit = (query: string) => {
    // Simply show the chat interface - no complex processing
    setSearchQuery(query);
    setShowChatInterface(true);
    setShowOrderGeneration(false);
  };
  const handleOrderGeneration = (query: string) => {
    // For replenishment orders, use the ChatInterface with sophisticated parsing
    if (query.toLowerCase().includes('replenishment')) {
      setSearchQuery(query);
      setShowChatInterface(true);
      setShowOrderGeneration(false);
    } else {
      // For simple orders, show the basic order generation interface
      setSearchQuery(query);
      setShowOrderGeneration(true);
      setShowChatInterface(false);
    }
  };
  const handleSuggestionClick = (suggestion: string) => {
    setSearchQuery(suggestion);
    handleChatSubmit(suggestion);
  };
  const handleOpenOrdersClick = () => {
    // "Open orders clicked");
    navigate('/orders');
  };
  const handleQuotesClick = () => {
    // "Quotes clicked");
    navigate('/quotes');
  };
  const handleApprovalsClick = () => {
    // "Approvals clicked");
    navigate('/approvals');
  };
  const handleNotificationsClick = () => {
    // "Notifications clicked");
    navigate('/notifications');
  };
  const totalSpend = monthlySpendData.reduce((sum, item) => sum + item.spend, 0);
  const kpiData = [{
    title: 'Open Orders',
    value: '27',
    icon: ClipboardList,
    borderColor: 'bg-green-500',
    bgColor: 'bg-gray-100',
    onClick: handleOpenOrdersClick
  }, {
    title: 'New Quotes Received',
    value: '2',
    icon: FileText,
    borderColor: 'bg-blue-500',
    bgColor: 'bg-gray-100',
    onClick: handleQuotesClick
  }, {
    title: 'Pending Approvals',
    value: '3',
    icon: Check,
    borderColor: 'bg-orange-500',
    bgColor: 'bg-gray-100',
    onClick: handleApprovalsClick
  }, {
    title: 'Notifications',
    value: '5',
    icon: Bell,
    borderColor: 'bg-purple-500',
    bgColor: 'bg-gray-100',
    onClick: handleNotificationsClick
  }];
  const handleNewQuery = () => {
    // Reset all chat-related states to return to main dashboard prompt box
    setShowChatInterface(false);
    setShowOrderGeneration(false);
    setSearchQuery('');
    setIsLoadingOrderSummary(false);
    setIsGeneratingPO(false);
  };

  if (!currentUser) return null;
  return <SidebarProvider>
      <div className="min-h-screen flex w-full bg-gray-100 dark:bg-black">
        <AppSidebar onLogout={handleLogout} onNewQuery={handleNewQuery} />
        <SidebarInset>
          <Header />
          
          <main className="flex-1 flex flex-col px-4 py-4">
            {isGeneratingPO ? <div className="flex items-center justify-center min-h-[80vh]">
                <PurchaseOrderGenerationTransition onComplete={handlePOGenerationComplete} />
              </div> : showOrderGeneration ? <div className="flex flex-col items-center justify-center w-full h-full bg-gray-900 text-white">
                <div className="max-w-md text-center">
                  <h2 className="text-2xl font-bold mb-4">Generating Purchase Order</h2>
                  <p className="text-gray-400 mb-6">Processing your order request: "{searchQuery}"</p>
                  <button onClick={() => setShowOrderGeneration(false)} className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                    Back to Search
                  </button>
                </div>
              </div> : showChatInterface ? <ChatInterface initialQuery={searchQuery} onSubmit={handleChatSubmit} /> : <div className="flex flex-col items-center justify-center w-full max-w-4xl mx-auto transition-all duration-500 ease-in-out mt-8" style={{
            minHeight: 'calc(100vh - 16rem)'
          }}>
                <div className="text-center mb-6 animate-in fade-in-0 slide-in-from-bottom-4 duration-700">
                  <h2 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl font-bold text-gray-800 dark:text-white mb-4 tracking-tight">What do you need to do today?</h2>
                  <p className="text-sm sm:text-base md:text-lg lg:text-xl text-gray-600 dark:text-gray-400 mb-4">Build forecasts, generate reports, and create purchase orders with ease.</p>
                </div>
                
                <div className="w-full max-w-3xl mx-auto animate-in fade-in-0 slide-in-from-bottom-6 duration-700 delay-200">
                  <SearchBar searchQuery={searchQuery} setSearchQuery={setSearchQuery} onSubmit={handleChatSubmit} onOrderGeneration={handleOrderGeneration} />
                </div>
                
                {/* System Prompts - Two on top, one on bottom */}
                <div className="w-full max-w-5xl mx-auto mt-4 space-y-2 animate-in fade-in-0 slide-in-from-bottom-8 duration-700 delay-400">
                  {/* Top row - two prompts side by side */}
                  <div className="flex flex-wrap gap-4 justify-center w-full">
                    <button
                      onClick={() => handleSuggestionClick("Re-order 100 units of black essential hoody XXL")}
                      className="px-6 py-3 text-sm font-bold text-gray-600 dark:text-gray-300 bg-white/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors backdrop-blur whitespace-nowrap"
                    >
                      "Re-order 100 units of black essential hoody XXL"
                    </button>
                    <button
                      onClick={() => handleSuggestionClick("Help me create a new forecast for SS25")}
                      className="px-6 py-3 text-sm font-bold text-gray-600 dark:text-gray-300 bg-white/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors backdrop-blur whitespace-nowrap"
                    >
                      "Help me create a new forecast for SS25"
                    </button>
                  </div>
                  {/* Bottom row - one prompt centered */}
                  <div className="flex justify-center">
                    <button
                      onClick={() => handleSuggestionClick("Identify stockouts across our best catagories and calculate missed sales")}
                      className="px-6 py-3 text-sm font-bold text-gray-600 dark:text-gray-300 bg-white/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-full hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors backdrop-blur whitespace-nowrap"
                    >
                      "Identify stockouts across our best catagories and calculate missed sales"
                    </button>
                  </div>
                </div>
              </div>}
          </main>
        </SidebarInset>
      </div>


      <PurchaseOrderPDFView isOpen={showPurchaseOrder} onOpenChange={setShowPurchaseOrder} orderData={selectedOrderData} />
    </SidebarProvider>;
};
export default Dashboard;
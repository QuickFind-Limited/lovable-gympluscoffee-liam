import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useNavigate,
} from "react-router-dom";
// import { ThemeProvider } from "next-themes";
import { Logger } from "@/services/Logger";
import {
  navigateToConversation,
  navigateToOrderSummary,
} from "@/utils/navigationUtils";
import Dashboard from "./pages/Dashboard";
import DataSources from "./pages/DataSources";
import Insights from "./pages/Insights";
import Suppliers from "./pages/Suppliers";

import Forecasts from "./pages/Forecasts";
import NotFound from "./pages/NotFound";
import OrderConfirmation from "./pages/OrderConfirmation";
import Orders from "./pages/Orders";
import OrderSummary from "./pages/OrderSummary";
import ProductDetails from "./pages/ProductDetails";
import ProductsCatalog from "./pages/ProductsCatalog";
import PurchaseOrderEditor from "./pages/PurchaseOrderEditor";
import Storage from "./pages/Storage";
import { ConversationProvider } from "./contexts/ConversationContext";
import { FinancialDataProvider } from "./contexts/FinancialDataContext";
import { UserProvider } from "./contexts/UserContext";

const DashboardWithNavigation = () => {
  const navigate = useNavigate();

  const handleNavigateToOrderSummary = (query: string) => {
    navigateToOrderSummary(navigate, query);
  };

  const handleNavigateToConversation = (message: string) => {
    navigateToConversation(navigate, message);
  };

  return (
    <Dashboard
      onNavigateToOrderSummary={handleNavigateToOrderSummary}
      onNavigateToConversation={handleNavigateToConversation}
    />
  );
};

const queryClient = new QueryClient();

const RoutesWithProviders = () => {
  return (
    <UserProvider>
      <FinancialDataProvider>
        <ConversationProvider>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardWithNavigation />} />
            <Route path="/data-sources" element={<DataSources />} />
            <Route path="/suppliers" element={<Suppliers />} />
            <Route path="/product/:id" element={<ProductDetails />} />
            <Route path="/order-summary" element={<OrderSummary />} />
            <Route path="/order-confirmation" element={<OrderConfirmation />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/purchase-order-editor" element={<PurchaseOrderEditor />} />
            <Route path="/products-catalog" element={<ProductsCatalog />} />
            <Route path="/forecasts" element={<Forecasts />} />
            <Route path="/insights" element={<Insights />} />
            <Route path="/storage" element={<Storage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </ConversationProvider>
      </FinancialDataProvider>
    </UserProvider>
  );
};

const App = () => {
  Logger.debug("App render - checking routes");

  return (
    <QueryClientProvider client={queryClient}>
      {/* <ThemeProvider attribute="class" defaultTheme="system" enableSystem> */}
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <RoutesWithProviders />
        </BrowserRouter>
      </TooltipProvider>
      {/* </ThemeProvider> */}
    </QueryClientProvider>
  );
};

export default App;

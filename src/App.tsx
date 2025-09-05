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
import Auth from "./pages/Auth";
import Dashboard from "./pages/Dashboard";
import DataSources from "./pages/DataSources";
import Insights from "./pages/Insights";
import Suppliers from "./pages/Suppliers";

import AuthConfirm from "./pages/AuthConfirm";
import Forecasts from "./pages/Forecasts";
import NotFound from "./pages/NotFound";
import OrderConfirmation from "./pages/OrderConfirmation";
import Orders from "./pages/Orders";
import OrderSummary from "./pages/OrderSummary";
import ProductDetails from "./pages/ProductDetails";
import ProductsCatalog from "./pages/ProductsCatalog";
import PurchaseOrderEditor from "./pages/PurchaseOrderEditor";
import Storage from "./pages/Storage";
import VerifyEmail from "./pages/VerifyEmail";

import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ConversationProvider } from "./contexts/ConversationContext";
import { FinancialDataProvider } from "./contexts/FinancialDataContext";
import { UserProvider } from "./contexts/UserContext";

const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-black border-t-transparent"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  return children;
};

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
    <AuthProvider>
      <UserProvider>
        <FinancialDataProvider>
          <ConversationProvider>
            <Routes>
              <Route path="/" element={<Navigate to="/auth" replace />} />
              <Route path="/auth" element={<Auth />} />
              <Route path="/auth/confirm" element={<AuthConfirm />} />
              <Route path="/verify-email" element={<VerifyEmail />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardWithNavigation />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/data-sources"
                element={
                  <ProtectedRoute>
                    <DataSources />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/suppliers"
                element={
                  <ProtectedRoute>
                    <Suppliers />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/product/:id"
                element={
                  <ProtectedRoute>
                    <ProductDetails />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/order-summary"
                element={
                  <ProtectedRoute>
                    <OrderSummary />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/order-confirmation"
                element={
                  <ProtectedRoute>
                    <OrderConfirmation />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/orders"
                element={
                  <ProtectedRoute>
                    <Orders />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/purchase-order-editor"
                element={
                  <ProtectedRoute>
                    <PurchaseOrderEditor />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/products-catalog"
                element={
                  <ProtectedRoute>
                    <ProductsCatalog />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/forecasts"
                element={
                  <ProtectedRoute>
                    <Forecasts />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/insights"
                element={
                  <ProtectedRoute>
                    <Insights />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/storage"
                element={
                  <ProtectedRoute>
                    <Storage />
                  </ProtectedRoute>
                }
              />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </ConversationProvider>
        </FinancialDataProvider>
      </UserProvider>
    </AuthProvider>
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

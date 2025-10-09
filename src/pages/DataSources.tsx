
import React from 'react';
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import DataSources from "@/components/DataSources";
import Header from "@/components/dashboard/Header";
import AppSidebar from '@/components/dashboard/AppSidebar';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { useNavigate } from 'react-router-dom';

const DataSourcesPage = () => {
  const { toast } = useToast();
  const navigate = useNavigate();

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <SidebarInset>
          <Header />
          <main className="flex-1 p-4">
            <DataSources />
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
};

export default DataSourcesPage;

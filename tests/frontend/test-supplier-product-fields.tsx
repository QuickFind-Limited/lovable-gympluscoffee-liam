import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Package, AlertCircle, Check, X } from "lucide-react";

// Extended interface with new fields
interface ExtendedSupplierProduct {
  id: number;
  product_id?: [number, string];
  product_name?: string;
  product_code?: string;
  
  // Existing fields
  min_qty?: number;  // This is MOQ
  price?: number;
  delay?: number;
  currency_id?: [number, string];
  
  // New fields from product.product
  qty_available?: number;       // Current stock available
  virtual_available?: number;   // Forecasted availability
  
  // New custom fields
  minimum_level?: number;       // Reorder point
  pack_size?: number;           // Units per package
  
  product_details?: {
    id: number;
    name: string;
    default_code?: string;
    qty_available?: number;
    virtual_available?: number;
    list_price?: number;
  };
}

// Mock data with new fields
const mockProducts: ExtendedSupplierProduct[] = [
  {
    id: 1,
    product_id: [123, "[ANF-00423] Premium Dog Food 15kg"],
    product_name: "Premium Dog Food 15kg",
    product_code: "ANF-00423",
    min_qty: 10,  // MOQ
    price: 45.99,
    delay: 3,
    qty_available: 150,
    virtual_available: 175,
    minimum_level: 50,
    pack_size: 6
  },
  {
    id: 2,
    product_id: [124, "[VET-00124] Cat Vitamin Supplements"],
    product_name: "Cat Vitamin Supplements",
    product_code: "VET-00124",
    min_qty: 24,  // MOQ
    price: 12.50,
    delay: 5,
    qty_available: 48,
    virtual_available: 48,
    minimum_level: 72,
    pack_size: 12
  },
  {
    id: 3,
    product_id: [125, "[TOY-00125] Interactive Dog Toy"],
    product_name: "Interactive Dog Toy",
    product_code: "TOY-00125",
    min_qty: 5,  // MOQ
    price: 8.99,
    delay: 2,
    qty_available: 0,
    virtual_available: 25,
    minimum_level: 20,
    pack_size: 1
  }
];

const TestSupplierProductFields: React.FC = () => {
  // Helper function to determine stock status
  const getStockStatus = (available: number = 0, minLevel: number = 0) => {
    if (available === 0) {
      return { color: "destructive", text: "Out of Stock", icon: <X className="h-3 w-3" /> };
    } else if (available < minLevel) {
      return { color: "warning", text: "Low Stock", icon: <AlertCircle className="h-3 w-3" /> };
    }
    return { color: "success", text: "In Stock", icon: <Check className="h-3 w-3" /> };
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Supplier Product Catalog - New Fields Test</CardTitle>
          <p className="text-muted-foreground mt-2">
            Testing display of new fields: Available, Minimum Level, Pack Size, and MOQ
          </p>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product</TableHead>
                  <TableHead className="text-center">Code</TableHead>
                  <TableHead className="text-center">Available</TableHead>
                  <TableHead className="text-center">Min Level</TableHead>
                  <TableHead className="text-center">Pack Size</TableHead>
                  <TableHead className="text-center">MOQ</TableHead>
                  <TableHead className="text-center">Price</TableHead>
                  <TableHead className="text-center">Lead Time</TableHead>
                  <TableHead className="text-center">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockProducts.map((product, index) => {
                  const stockStatus = getStockStatus(product.qty_available, product.minimum_level);
                  return (
                    <TableRow key={product.id} className={index % 2 === 0 ? 'bg-background' : 'bg-muted/20'}>
                      <TableCell>
                        <div className="font-medium">{product.product_name}</div>
                      </TableCell>
                      <TableCell className="text-center font-mono text-sm">
                        {product.product_code || '-'}
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex flex-col items-center">
                          <span className="font-medium">{product.qty_available || 0}</span>
                          {product.virtual_available !== product.qty_available && (
                            <span className="text-xs text-muted-foreground">
                              ({product.virtual_available} forecast)
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        {product.minimum_level || '-'}
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex items-center justify-center gap-1">
                          <Package className="h-3 w-3 text-muted-foreground" />
                          {product.pack_size || 1}
                        </div>
                      </TableCell>
                      <TableCell className="text-center font-medium">
                        {product.min_qty || 1}
                      </TableCell>
                      <TableCell className="text-center">
                        {product.price ? `$${product.price.toFixed(2)}` : '-'}
                      </TableCell>
                      <TableCell className="text-center">
                        {product.delay ? `${product.delay} days` : '-'}
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge 
                          variant={stockStatus.color as any}
                          className="flex items-center gap-1 justify-center"
                        >
                          {stockStatus.icon}
                          {stockStatus.text}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
          
          <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4 border-2">
              <h3 className="font-semibold text-sm mb-2">Available</h3>
              <p className="text-xs text-muted-foreground">
                Current stock quantity available for ordering. Shows both on-hand and forecasted quantities.
              </p>
            </Card>
            <Card className="p-4 border-2">
              <h3 className="font-semibold text-sm mb-2">Minimum Level</h3>
              <p className="text-xs text-muted-foreground">
                Reorder point - when stock drops below this level, it's time to reorder from the supplier.
              </p>
            </Card>
            <Card className="p-4 border-2">
              <h3 className="font-semibold text-sm mb-2">Pack Size</h3>
              <p className="text-xs text-muted-foreground">
                Units per package - how many individual units come in one supplier package.
              </p>
            </Card>
            <Card className="p-4 border-2">
              <h3 className="font-semibold text-sm mb-2">MOQ</h3>
              <p className="text-xs text-muted-foreground">
                Minimum Order Quantity - the smallest quantity the supplier will accept for an order.
              </p>
            </Card>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Field Source Mapping</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p><strong>Available:</strong> From product.product model → qty_available field</p>
            <p><strong>Minimum Level:</strong> Custom field or from stock.warehouse.orderpoint model</p>
            <p><strong>Pack Size:</strong> From product.packaging model or custom field</p>
            <p><strong>MOQ:</strong> From product.supplierinfo model → min_qty field (already exists)</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TestSupplierProductFields;
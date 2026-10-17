// frontend/src/hooks/useShipment.ts
import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

interface ShipmentContextValue {
  shipmentId: string | null;
  setShipmentId: (id: string | null) => void;
}

const ShipmentContext = createContext<ShipmentContextValue>({
  shipmentId: null,
  setShipmentId: () => {},
});

export function ShipmentProvider({ children }: { children: ReactNode }) {
  const [shipmentId, setShipmentId] = useState<string | null>(
    () => sessionStorage.getItem('clearancex_shipment_id')
  );

  const handleSet = useCallback((id: string | null) => {
    setShipmentId(id);
    if (id) sessionStorage.setItem('clearancex_shipment_id', id);
    else sessionStorage.removeItem('clearancex_shipment_id');
  }, []);

  return (
    <ShipmentContext.Provider value={{ shipmentId, setShipmentId: handleSet }}>
      {children}
    </ShipmentContext.Provider>
  );
}

export function useShipment(): ShipmentContextValue {
  return useContext(ShipmentContext);
}

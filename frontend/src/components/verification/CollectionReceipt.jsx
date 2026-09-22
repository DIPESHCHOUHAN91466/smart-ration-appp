import { CheckCircle2, Download } from "lucide-react";

export default function CollectionReceipt({ receipt, onDone }) {
  return (
    <section className="panel confirmation">
      <div className="success-circle">
        <CheckCircle2 size={42} />
      </div>
      <h2>Ration Collection Successful</h2>
      <p className="muted">The beneficiary's ration has been issued and recorded.</p>
      <div className="summary">
        <div>
          <span>Collection ID</span>
          <b>{receipt.collectionCode}</b>
        </div>
        <div>
          <span>Token</span>
          <b>{receipt.tokenNumber}</b>
        </div>
        <div>
          <span>Beneficiary</span>
          <b>
            {receipt.beneficiaryName} ({receipt.familySize} family members)
          </b>
        </div>
        <div>
          <span>Scheme</span>
          <b>{receipt.schemeCode}</b>
        </div>
        <div>
          <span>Items Issued</span>
          <b>{receipt.issuedItems.map((i) => `${i.rationType} ${i.quantity}kg`).join(" • ")}</b>
        </div>
        <div>
          <span>Total Quantity</span>
          <b>{receipt.totalQuantityKg} kg</b>
        </div>
        <div>
          <span>Shop</span>
          <b>{receipt.shopName}</b>
        </div>
        <div>
          <span>Date &amp; Time</span>
          <b>{receipt.collectedAt}</b>
        </div>
      </div>
      <div className="actions">
        <button className="secondary-btn" onClick={() => window.print()}>
          <Download /> Print Receipt
        </button>
        <button className="primary-btn" onClick={onDone}>
          Scan Next Beneficiary
        </button>
      </div>
    </section>
  );
}

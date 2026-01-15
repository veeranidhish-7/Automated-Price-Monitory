import { Trash2, ExternalLink, TrendingDown, TrendingUp } from "lucide-react";

export default function ProductCard({ product, onDelete }) {
  // Safe check for numbers to prevent errors if data is missing
  const currentPrice = product.current_price || 0;
  const targetPrice = product.target_price || 0;

  const isPriceBelow = currentPrice <= targetPrice;
  const priceDiff = Math.abs(currentPrice - targetPrice).toFixed(2);

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-xl transition p-6 border border-gray-100">
      {/* Site Badge */}
      <div className="flex items-center justify-between mb-4">
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold ${
            product.site_source === "amazon"
              ? "bg-orange-100 text-orange-700"
              : "bg-yellow-100 text-yellow-700"
          }`}
        >
          {product.site_source === "amazon" ? "📦 Amazon" : "🛒 Flipkart"}
        </span>

        <button
          onClick={() => onDelete(product.id)}
          className="text-red-500 hover:bg-red-50 p-2 rounded-lg transition"
          title="Delete product"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Product Title */}
      <h3 className="text-lg font-semibold text-gray-800 mb-3 line-clamp-2 min-h-14">
        {product.product_title}
      </h3>

      {/* Price Info */}
      <div className="space-y-3 mb-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Current Price</span>
          <span className="text-2xl font-bold text-gray-900">
            ₹{currentPrice.toFixed(2)}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Target Price</span>
          <span className="text-lg font-semibold text-indigo-600">
            ₹{targetPrice.toFixed(2)}
          </span>
        </div>

        {/* Price Status */}
        <div
          className={`flex items-center gap-2 p-3 rounded-lg ${
            isPriceBelow ? "bg-green-50" : "bg-yellow-50"
          }`}
        >
          {isPriceBelow ? (
            <>
              <TrendingDown className="w-5 h-5 text-green-600" />
              <span className="text-sm text-green-700 font-medium">
                ₹{priceDiff} below target! 🎉
              </span>
            </>
          ) : (
            <>
              <TrendingUp className="w-5 h-5 text-yellow-600" />
              <span className="text-sm text-yellow-700 font-medium">
                ₹{priceDiff} above target
              </span>
            </>
          )}
        </div>
      </div>

      {/* View Product Button (FIXED SECTION) */}
      <a
        href={product.url}
        target="_blank"
        rel="noopener noreferrer"
        className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-2 rounded-lg font-medium hover:bg-indigo-700 transition"
      >
        View Product
        <ExternalLink className="w-4 h-4" />
      </a>

      {/* Last Checked */}
      <p className="text-xs text-gray-500 text-center mt-3">
        Last checked:{" "}
        {product.last_checked
          ? new Date(product.last_checked).toLocaleString()
          : "Just now"}
      </p>
    </div>
  );
}

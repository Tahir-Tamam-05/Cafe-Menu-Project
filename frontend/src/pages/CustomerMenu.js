import { useState, useEffect } from "react";
import axios from "axios";
import { Coffee, Star, Filter, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CustomerMenu = () => {
  const [menuItems, setMenuItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMenu();
    fetchCategories();
  }, []);

  const fetchMenu = async () => {
    try {
      const response = await axios.get(`${API}/menu`);
      setMenuItems(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching menu:", error);
      toast.error("Failed to load menu");
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/menu/categories`);
      setCategories(["All", ...response.data.categories]);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  const filteredItems = selectedCategory === "All"
    ? menuItems
    : menuItems.filter(item => item.category === selectedCategory);

  const specialItems = menuItems.filter(item => item.is_special);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FBF8F3] via-[#F5E6D3] to-[#EAD5B8]">
      <Toaster position="top-center" />
      
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/80 border-b border-[#D4A574] shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#8B6F47] to-[#6B4423] flex items-center justify-center shadow-md">
                <Coffee className="w-7 h-7 text-[#F5E6D3]" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-[#6B4423]" data-testid="cafe-title">Lassi Day Café</h1>
                <p className="text-sm text-[#8B6F47]">Fresh & Delicious</p>
              </div>
            </div>
            <a href="/admin/login">
              <Button 
                variant="outline" 
                className="border-[#8B6F47] text-[#6B4423] hover:bg-[#F5E6D3] hover:border-[#6B4423]"
                data-testid="admin-login-btn"
              >
                Admin
              </Button>
            </a>
          </div>
        </div>
      </header>

      {/* Today's Specials */}
      {specialItems.length > 0 && (
        <section className="bg-gradient-to-r from-[#8B6F47] to-[#6B4423] text-white py-8 shadow-lg" data-testid="specials-section">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-2 mb-4">
              <Star className="w-6 h-6 fill-[#F5E6D3] text-[#F5E6D3]" />
              <h2 className="text-3xl font-bold">Today's Specials</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {specialItems.map(item => (
                <div 
                  key={item.id} 
                  className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20 hover:bg-white/20 transition-all"
                  data-testid={`special-item-${item.id}`}
                >
                  <h3 className="font-semibold text-lg">{item.name}</h3>
                  <p className="text-[#F5E6D3] text-sm mt-1">{item.description}</p>
                  <p className="text-xl font-bold mt-2">₹{item.price}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Category Filter */}
      <div className="sticky top-[73px] z-40 bg-white/90 backdrop-blur-md border-b border-[#D4A574] shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-2 mb-3">
            <Filter className="w-5 h-5 text-[#6B4423]" />
            <h3 className="font-semibold text-[#6B4423]">Filter by Category</h3>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide" data-testid="category-filter">
            {categories.map(category => (
              <Button
                key={category}
                onClick={() => setSelectedCategory(category)}
                variant={selectedCategory === category ? "default" : "outline"}
                className={selectedCategory === category 
                  ? "bg-[#6B4423] text-white hover:bg-[#8B6F47] whitespace-nowrap" 
                  : "border-[#8B6F47] text-[#6B4423] hover:bg-[#F5E6D3] whitespace-nowrap"
                }
                data-testid={`category-${category}`}
              >
                {category}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Menu Items */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="text-center py-20">
            <Coffee className="w-16 h-16 text-[#8B6F47] animate-spin mx-auto mb-4" />
            <p className="text-[#6B4423] text-lg">Loading delicious menu...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredItems.map(item => (
              <div 
                key={item.id}
                className="group bg-white rounded-xl shadow-md hover:shadow-xl border border-[#E8D5C0] overflow-hidden transition-all hover:-translate-y-1"
                data-testid={`menu-item-${item.id}`}
              >
                <div className="h-40 bg-gradient-to-br from-[#F5E6D3] to-[#EAD5B8] flex items-center justify-center relative overflow-hidden">
                  {item.is_special && (
                    <Badge className="absolute top-2 right-2 bg-[#6B4423] text-white">
                      <Star className="w-3 h-3 mr-1 fill-white" />
                      Special
                    </Badge>
                  )}
                  <Coffee className="w-20 h-20 text-[#8B6F47] group-hover:scale-110 transition-transform" />
                </div>
                <div className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-lg text-[#6B4423] line-clamp-1">{item.name}</h3>
                    <span className="text-xl font-bold text-[#8B6F47] whitespace-nowrap ml-2">₹{item.price}</span>
                  </div>
                  {item.description && (
                    <p className="text-sm text-[#8B6F47] line-clamp-2 mb-3">{item.description}</p>
                  )}
                  <Badge variant="outline" className="border-[#D4A574] text-[#6B4423] text-xs">
                    {item.category}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && filteredItems.length === 0 && (
          <div className="text-center py-20">
            <Coffee className="w-16 h-16 text-[#8B6F47] mx-auto mb-4 opacity-50" />
            <p className="text-[#6B4423] text-lg">No items found in this category</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gradient-to-r from-[#6B4423] to-[#8B6F47] text-white py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Coffee className="w-6 h-6" />
            <h3 className="text-xl font-bold">Lassi Day Café</h3>
          </div>
          <p className="text-[#F5E6D3] text-sm">© 2025 Lassi Day Café. All rights reserved.</p>
          <p className="text-[#F5E6D3] text-xs mt-2">Made with ❤️ for food lovers</p>
        </div>
      </footer>
    </div>
  );
};

export default CustomerMenu;

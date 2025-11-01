import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Coffee, Plus, Edit, Trash2, Star, Eye, EyeOff, LogOut, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [menuItems, setMenuItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    category: "",
    price: "",
    description: "",
    image_url: "",
    is_special: false,
    available: true
  });

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) {
      navigate("/admin/login");
      return;
    }
    fetchMenuItems();
    fetchCategories();
  }, [navigate]);

  const getAuthHeader = () => {
    return { headers: { Authorization: `Bearer ${localStorage.getItem("adminToken")}` } };
  };

  const fetchMenuItems = async () => {
    try {
      const response = await axios.get(`${API}/admin/menu`, getAuthHeader());
      setMenuItems(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching menu items:", error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        toast.error("Session expired. Please login again.");
        localStorage.removeItem("adminToken");
        navigate("/admin/login");
      }
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/menu/categories`);
      setCategories(response.data.categories);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("adminToken");
    toast.success("Logged out successfully");
    navigate("/admin/login");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.category || !formData.price) {
      toast.error("Please fill all required fields");
      return;
    }

    try {
      if (editingItem) {
        // Update existing item
        await axios.put(
          `${API}/admin/menu/${editingItem.id}`,
          {
            ...formData,
            price: parseFloat(formData.price)
          },
          getAuthHeader()
        );
        toast.success("Item updated successfully!");
      } else {
        // Create new item
        await axios.post(
          `${API}/admin/menu`,
          {
            ...formData,
            price: parseFloat(formData.price)
          },
          getAuthHeader()
        );
        toast.success("Item created successfully!");
      }
      
      setDialogOpen(false);
      resetForm();
      fetchMenuItems();
    } catch (error) {
      console.error("Error saving item:", error);
      toast.error(error.response?.data?.detail || "Failed to save item");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this item?")) return;

    try {
      await axios.delete(`${API}/admin/menu/${id}`, getAuthHeader());
      toast.success("Item deleted successfully!");
      fetchMenuItems();
    } catch (error) {
      console.error("Error deleting item:", error);
      toast.error("Failed to delete item");
    }
  };

  const handleToggleSpecial = async (id) => {
    try {
      await axios.put(`${API}/admin/menu/${id}/toggle-special`, {}, getAuthHeader());
      toast.success("Special status updated!");
      fetchMenuItems();
    } catch (error) {
      console.error("Error toggling special:", error);
      toast.error("Failed to update special status");
    }
  };

  const handleToggleAvailable = async (id) => {
    try {
      await axios.put(`${API}/admin/menu/${id}/toggle-available`, {}, getAuthHeader());
      toast.success("Availability updated!");
      fetchMenuItems();
    } catch (error) {
      console.error("Error toggling availability:", error);
      toast.error("Failed to update availability");
    }
  };

  const openEditDialog = (item) => {
    setEditingItem(item);
    setFormData({
      name: item.name,
      category: item.category,
      price: item.price.toString(),
      description: item.description || "",
      image_url: item.image_url || "",
      is_special: item.is_special,
      available: item.available
    });
    setDialogOpen(true);
  };

  const openCreateDialog = () => {
    resetForm();
    setDialogOpen(true);
  };

  const resetForm = () => {
    setEditingItem(null);
    setFormData({
      name: "",
      category: "",
      price: "",
      description: "",
      image_url: "",
      is_special: false,
      available: true
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FBF8F3] via-[#F5E6D3] to-[#EAD5B8]">
      <Toaster position="top-center" />
      
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-md border-b-2 border-[#D4A574] shadow-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#8B6F47] to-[#6B4423] flex items-center justify-center shadow-md">
                <Coffee className="w-7 h-7 text-[#F5E6D3]" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-[#6B4423]" data-testid="admin-dashboard-title">Admin Dashboard</h1>
                <p className="text-sm text-[#8B6F47]">Manage your café menu</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                className="border-[#8B6F47] text-[#6B4423] hover:bg-[#F5E6D3]"
                onClick={() => navigate("/")}
                data-testid="view-menu-btn"
              >
                View Menu
              </Button>
              <Button
                variant="outline"
                className="border-red-300 text-red-600 hover:bg-red-50"
                onClick={handleLogout}
                data-testid="logout-btn"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
          <Card className="border-2 border-[#D4A574]">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-[#8B6F47]">Total Items</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-[#6B4423]" data-testid="total-items">{menuItems.length}</p>
            </CardContent>
          </Card>
          <Card className="border-2 border-[#D4A574]">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-[#8B6F47]">Available Items</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-green-600" data-testid="available-items">
                {menuItems.filter(item => item.available).length}
              </p>
            </CardContent>
          </Card>
          <Card className="border-2 border-[#D4A574]">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-[#8B6F47]">Today's Specials</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-amber-600" data-testid="special-items">
                {menuItems.filter(item => item.is_special).length}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Add New Item Button */}
        <div className="mb-6">
          <Button
            onClick={openCreateDialog}
            className="bg-[#6B4423] hover:bg-[#8B6F47] text-white shadow-lg"
            data-testid="add-item-btn"
          >
            <Plus className="w-5 h-5 mr-2" />
            Add New Item
          </Button>
        </div>

        {/* Menu Items Grid */}
        {loading ? (
          <div className="text-center py-20">
            <Coffee className="w-16 h-16 text-[#8B6F47] animate-spin mx-auto mb-4" />
            <p className="text-[#6B4423] text-lg">Loading menu items...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {menuItems.map(item => (
              <Card key={item.id} className="border-2 border-[#D4A574] hover:shadow-xl transition-shadow" data-testid={`admin-menu-item-${item.id}`}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg text-[#6B4423] mb-1">{item.name}</CardTitle>
                      <Badge variant="outline" className="border-[#D4A574] text-[#6B4423] text-xs">
                        {item.category}
                      </Badge>
                    </div>
                    <span className="text-xl font-bold text-[#8B6F47]">₹{item.price}</span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {item.description && (
                    <p className="text-sm text-[#8B6F47] line-clamp-2">{item.description}</p>
                  )}
                  
                  {/* Toggles */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2 bg-amber-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Star className={`w-4 h-4 ${item.is_special ? 'fill-amber-500 text-amber-500' : 'text-gray-400'}`} />
                        <span className="text-sm font-medium text-[#6B4423]">Today's Special</span>
                      </div>
                      <Switch
                        checked={item.is_special}
                        onCheckedChange={() => handleToggleSpecial(item.id)}
                        data-testid={`toggle-special-${item.id}`}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between p-2 bg-green-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        {item.available ? (
                          <Eye className="w-4 h-4 text-green-600" />
                        ) : (
                          <EyeOff className="w-4 h-4 text-gray-400" />
                        )}
                        <span className="text-sm font-medium text-[#6B4423]">Available</span>
                      </div>
                      <Switch
                        checked={item.available}
                        onCheckedChange={() => handleToggleAvailable(item.id)}
                        data-testid={`toggle-available-${item.id}`}
                      />
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-2">
                    <Button
                      variant="outline"
                      className="flex-1 border-[#8B6F47] text-[#6B4423] hover:bg-[#F5E6D3]"
                      onClick={() => openEditDialog(item)}
                      data-testid={`edit-item-${item.id}`}
                    >
                      <Edit className="w-4 h-4 mr-1" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1 border-red-300 text-red-600 hover:bg-red-50"
                      onClick={() => handleDelete(item.id)}
                      data-testid={`delete-item-${item.id}`}
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl text-[#6B4423]">
              {editingItem ? "Edit Menu Item" : "Add New Menu Item"}
            </DialogTitle>
            <DialogDescription className="text-[#8B6F47]">
              {editingItem ? "Update the menu item details" : "Fill in the details for the new menu item"}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name" className="text-[#6B4423]">Item Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="border-[#D4A574] focus:border-[#8B6F47]"
                  placeholder="e.g., Sweet Lassi"
                  required
                  data-testid="item-name-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="category" className="text-[#6B4423]">Category *</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => setFormData({...formData, category: value})}
                  data-testid="item-category-select"
                >
                  <SelectTrigger className="border-[#D4A574] focus:border-[#8B6F47]">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map(cat => (
                      <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                    ))}
                    <SelectItem value="New Category">+ Add New Category</SelectItem>
                  </SelectContent>
                </Select>
                {formData.category === "New Category" && (
                  <Input
                    placeholder="Enter new category name"
                    value={formData.category === "New Category" ? "" : formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    className="border-[#D4A574] mt-2"
                  />
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="price" className="text-[#6B4423]">Price (₹) *</Label>
              <Input
                id="price"
                type="number"
                step="0.01"
                value={formData.price}
                onChange={(e) => setFormData({...formData, price: e.target.value})}
                className="border-[#D4A574] focus:border-[#8B6F47]"
                placeholder="e.g., 80"
                required
                data-testid="item-price-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description" className="text-[#6B4423]">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                className="border-[#D4A574] focus:border-[#8B6F47] min-h-[80px]"
                placeholder="Brief description of the item"
                data-testid="item-description-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="image_url" className="text-[#6B4423]">Image URL</Label>
              <Input
                id="image_url"
                value={formData.image_url}
                onChange={(e) => setFormData({...formData, image_url: e.target.value})}
                className="border-[#D4A574] focus:border-[#8B6F47]"
                placeholder="https://example.com/image.jpg"
                data-testid="item-image-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2 p-3 bg-amber-50 rounded-lg">
                <Switch
                  id="is_special"
                  checked={formData.is_special}
                  onCheckedChange={(checked) => setFormData({...formData, is_special: checked})}
                  data-testid="item-special-toggle"
                />
                <Label htmlFor="is_special" className="text-[#6B4423] cursor-pointer">
                  Mark as Today's Special
                </Label>
              </div>

              <div className="flex items-center space-x-2 p-3 bg-green-50 rounded-lg">
                <Switch
                  id="available"
                  checked={formData.available}
                  onCheckedChange={(checked) => setFormData({...formData, available: checked})}
                  data-testid="item-available-toggle"
                />
                <Label htmlFor="available" className="text-[#6B4423] cursor-pointer">
                  Available
                </Label>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="submit"
                className="flex-1 bg-[#6B4423] hover:bg-[#8B6F47] text-white"
                data-testid="submit-item-btn"
              >
                {editingItem ? "Update Item" : "Add Item"}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="flex-1 border-[#8B6F47] text-[#6B4423] hover:bg-[#F5E6D3]"
                onClick={() => {
                  setDialogOpen(false);
                  resetForm();
                }}
                data-testid="cancel-item-btn"
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminDashboard;

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Coffee, Mail, Lock, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from "@/components/ui/input-otp";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminLogin = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState(1); // 1: email, 2: otp
  const [loading, setLoading] = useState(false);

  const handleSendOTP = async (e) => {
    e.preventDefault();
    
    if (!email) {
      toast.error("Please enter your email");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/auth/send-otp`, { email });
      toast.success("OTP sent to your email!");
      setStep(2);
    } catch (error) {
      console.error("Error sending OTP:", error);
      toast.error(error.response?.data?.detail || "Failed to send OTP");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    
    if (otp.length !== 6) {
      toast.error("Please enter 6-digit OTP");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/verify-otp`, { email, otp });
      localStorage.setItem("adminToken", response.data.token);
      toast.success("Login successful!");
      setTimeout(() => navigate("/admin/dashboard"), 500);
    } catch (error) {
      console.error("Error verifying OTP:", error);
      toast.error(error.response?.data?.detail || "Invalid OTP");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FBF8F3] via-[#F5E6D3] to-[#EAD5B8] flex items-center justify-center p-4">
      <Toaster position="top-center" />
      
      <div className="w-full max-w-md">
        {/* Back Button */}
        <Button
          variant="ghost"
          className="mb-4 text-[#6B4423] hover:bg-[#F5E6D3]"
          onClick={() => navigate("/")}
          data-testid="back-to-menu-btn"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Menu
        </Button>

        <Card className="border-2 border-[#D4A574] shadow-xl">
          <CardHeader className="space-y-3">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#8B6F47] to-[#6B4423] flex items-center justify-center mx-auto shadow-lg">
              <Coffee className="w-9 h-9 text-[#F5E6D3]" />
            </div>
            <CardTitle className="text-2xl text-center text-[#6B4423]" data-testid="admin-login-title">
              Admin Login
            </CardTitle>
            <CardDescription className="text-center text-[#8B6F47]">
              {step === 1 ? "Enter your email to receive OTP" : "Enter the OTP sent to your email"}
            </CardDescription>
          </CardHeader>

          <CardContent>
            {step === 1 ? (
              <form onSubmit={handleSendOTP} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-[#6B4423]">Email Address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8B6F47]" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="admin@lassidaycafe.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-10 border-[#D4A574] focus:border-[#8B6F47] focus:ring-[#8B6F47]"
                      data-testid="email-input"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-[#6B4423] hover:bg-[#8B6F47] text-white"
                  disabled={loading}
                  data-testid="send-otp-btn"
                >
                  {loading ? "Sending..." : "Send OTP"}
                </Button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOTP} className="space-y-6">
                <div className="space-y-3">
                  <Label htmlFor="otp" className="text-[#6B4423] text-center block">Enter 6-Digit OTP</Label>
                  <div className="flex justify-center">
                    <InputOTP
                      maxLength={6}
                      value={otp}
                      onChange={(value) => setOtp(value)}
                      data-testid="otp-input"
                    >
                      <InputOTPGroup>
                        <InputOTPSlot index={0} className="border-[#D4A574]" />
                        <InputOTPSlot index={1} className="border-[#D4A574]" />
                        <InputOTPSlot index={2} className="border-[#D4A574]" />
                        <InputOTPSlot index={3} className="border-[#D4A574]" />
                        <InputOTPSlot index={4} className="border-[#D4A574]" />
                        <InputOTPSlot index={5} className="border-[#D4A574]" />
                      </InputOTPGroup>
                    </InputOTP>
                  </div>
                  <p className="text-xs text-center text-[#8B6F47]">OTP sent to: {email}</p>
                </div>

                <div className="space-y-2">
                  <Button
                    type="submit"
                    className="w-full bg-[#6B4423] hover:bg-[#8B6F47] text-white"
                    disabled={loading || otp.length !== 6}
                    data-testid="verify-otp-btn"
                  >
                    {loading ? "Verifying..." : "Verify & Login"}
                  </Button>
                  
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full border-[#8B6F47] text-[#6B4423] hover:bg-[#F5E6D3]"
                    onClick={() => {
                      setStep(1);
                      setOtp("");
                    }}
                    data-testid="change-email-btn"
                  >
                    Change Email
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>

        <p className="text-center text-sm text-[#8B6F47] mt-4">
          OTP is valid for 10 minutes
        </p>
      </div>
    </div>
  );
};

export default AdminLogin;

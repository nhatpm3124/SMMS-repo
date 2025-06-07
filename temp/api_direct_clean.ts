// API service for handling all backend requests
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';


interface LoginCredentials {
  username: string;
  password: string;
}

interface LoginWith2FACredentials {
  username: string;
  password: string;
  token: string;
}

export interface UserData {
  username: string;
  fullName: string;
  email: string;
  password?: string;  // Password is now optional
  phone?: string;
  area?: string;
  house?: string;
  role?: 'root' | 'admin' | 'mentor' | 'brosis';
  status?: 'active' | 'inactive';
}

// Adding a separate interface for user updates
export interface UserUpdateData {
  fullName?: string;
  email?: string;
  phone?: string;
  area?: string;
  house?: string;
  role?: 'admin' | 'mentor' | 'brosis';
  status?: 'active' | 'inactive';
}

interface ApiResponse<T> {
  data?: T;
  error?: string;
  debug?: any; // Add debug property to support debug information
}

interface ChangePasswordData {
  current_password: string;
  new_password: string;
}

interface AreaData {
  name: string;
}

interface HouseData {
  name: string;
  areaId: number;
}

interface BulkOperationPayload {
  mode: 'all' | 'selected';
  userIds: number[]; // Empty array when mode is 'all'
}

interface BulkStatusChangePayload extends BulkOperationPayload {
  action: 'activate' | 'deactivate';
}

interface BulkResetPasswordsPayload extends BulkOperationPayload {
  // No additional fields needed, inherits mode and userIds from BulkOperationPayload
}

interface UserFilters {
  search?: string;
  role?: string;
  status?: string;
  area?: string;
  house?: string;
}

interface StudentFilters {
  search?: string;
  status?: string;
  matched?: string;
  area?: string;
  house?: string;
}

export interface ExportUsersPayload {
  mode: 'all' | 'selected';
  userIds: number[];
  format?: 'csv' | 'excel';
  filters?: UserFilters;
}

interface BulkOperationResult {
  success: number;
  failed: number;
  skipped: number;
}

// Get the authentication token from local storage
const getToken = (): string | null => {
  return localStorage.getItem('token');
};

// API Service with methods for all backend interactions
const ApiService = {
  // Authentication
  login: async (credentials: LoginCredentials): Promise<ApiResponse<any>> => {
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Login failed' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Login with 2FA
  loginWith2FA: async (credentials: LoginWith2FACredentials): Promise<ApiResponse<any>> => {
    try {
      console.log('Sending 2FA login request with token');
      
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });
      
      const data = await response.json();
      console.log('2FA login response:', data);
      
      if (!response.ok) {
        console.error('2FA login failed:', data);
        return { error: data.error || 'Two-factor authentication failed' };
      }
      
      if (data.requires_2fa) {
        console.error('Still requiring 2FA after submitting token');
        return { error: 'Invalid authentication code' };
      }

      if (data.requires_2fa_setup) {
        console.error('Still requiring 2FA setup');
        return { error: data.message || 'Root account requires 2FA setup' };
      }
      
      console.log('2FA login successful');
      return { data };
    } catch (error) {
      console.error('2FA login network error:', error);
      return { error: 'Network error, please try again' };
    }
  },
  
  // Get hello message (public)
  getHello: async (): Promise<ApiResponse<any>> => {
    try {
      const response = await fetch(`${API_BASE_URL}/hello`);
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to fetch message' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Get users (protected)
  getUsers: async (page?: number, perPage?: number, filters?: {
    searchTerm?: string,
    role?: string,
    status?: string,
    area?: string,
    house?: string
  }): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      // Construct URL with pagination parameters
      let url = `${API_BASE_URL}/users`;
      
      // Add query params
      const queryParams: string[] = [];
      
      // Add pagination params
      if (page !== undefined && perPage !== undefined) {
        queryParams.push(`page=${page}`);
        queryParams.push(`per_page=${perPage}`);
      }
      
      // Add filter params if they exist
      if (filters) {
        if (filters.searchTerm) {
          queryParams.push(`search=${encodeURIComponent(filters.searchTerm)}`);
        }
        
        if (filters.role && filters.role !== 'all') {
          // Make sure we're using lowercase role values to match backend expectations
          queryParams.push(`role=${encodeURIComponent(filters.role.toLowerCase())}`);
        }
        
        if (filters.status && filters.status !== 'all') {
          queryParams.push(`status=${encodeURIComponent(filters.status)}`);
        }
          
        if (filters.area && filters.area !== 'all') {
          queryParams.push(`area=${encodeURIComponent(filters.area)}`);
        }
          
        if (filters.house && filters.house !== 'all') {
          queryParams.push(`house=${encodeURIComponent(filters.house)}`);
        }
        
        console.log("Applied filters:", filters);
      }
      
      // Append query string if we have params
      if (queryParams.length > 0) {
        // Đơn giản hóa tham số, chỉ sử dụng mảng queryParams
        // Vì chúng ta đã đảm bảo không thêm các tham số trùng lặp ở trên
        url = `${url}?${queryParams.join('&')}`;
        
        // Log URL để debug
        console.log("Final URL with filters:", url);
      }
      
      console.log("API URL with filters:", url);
      
      // Prepare debug info
      const debugInfo = {
        apiUrl: url,
        filterParams: {},
        serverResponse: null
      };
      
      // Add filter params to debug info
      if (filters) {
        debugInfo.filterParams = { ...filters };
      }
      
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10-second timeout
        
        const response = await fetch(url, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json'
          },
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const data = await response.json();
        debugInfo.serverResponse = data;
        
        if (!response.ok) {
          return { error: data.error || 'Failed to fetch users', debug: debugInfo };
        }
        
        return { data, debug: debugInfo };
      } catch (fetchError: unknown) {
        if (typeof fetchError === 'object' && fetchError !== null && 'name' in fetchError && fetchError.name === 'AbortError') {
          return { error: 'Request timed out. The server may be overloaded.' };
        }
        return { error: 'Network error, please try again' };
      }
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Create user (protected)
  createUser: async (userData: UserData): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      console.log("Creating user with data:", JSON.stringify(userData, null, 2));
      console.log("API URL:", `${API_BASE_URL}/users`);
      
      const response = await fetch(`${API_BASE_URL}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(userData),
      });
      
      // First check if response is OK before parsing JSON
      if (!response.ok) {
        try {
          const errorData = await response.json();
          return { error: errorData.error || errorData.message || `Server error: ${response.status}` };
        } catch (jsonError) {
          // If can't parse JSON, get text
          const errorText = await response.text();
          console.error("Failed to parse server response as JSON:", errorText);
          return { error: `Server error ${response.status}: ${errorText.substring(0, 100)}...` };
        }
      }
      
      // Parse JSON response
      try {
        const data = await response.json();
        console.log("User creation successful:", data);
        return { data, debug: { url: `${API_BASE_URL}/users`, status: response.status } };
      } catch (jsonError) {
        console.error("Error parsing successful response:", jsonError);
        return { error: 'Invalid response format from server' };
      }
    } catch (error: any) {
      console.error("Network error during user creation:", error);
      return { error: `Network error: ${error.message || 'Failed to connect to server'}` };
    }
  },
  
  // Update an existing user
  updateUser: async (userId: number, userData: UserUpdateData): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      console.log("Updating user with data:", JSON.stringify(userData, null, 2));
      
      const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(userData),
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        return { 
          error: result.message || 'Error updating user',
          debug: result // Pass debug info 
        };
      }
      
      return { 
        data: result,
        debug: result // Pass debug info
      };
    } catch (error) {
      console.error('Error updating user:', error);
      return { 
        error: (error as Error).message || 'Unknown error occurred',
        debug: error // Pass debug info
      };
    }
  },
  
  // Toggle user status (active/inactive) (protected)
  toggleUserStatus: async (userId: number): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      // We'll let the browser handle the preflight request automatically
      // No need to manually send OPTIONS request
      
      const response = await fetch(`${API_BASE_URL}/users/${userId}/toggle-status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        // Default is 'same-origin', let's use 'cors'
        mode: 'cors'
      });
      
      // Handle non-JSON responses
      let data;
      const contentType = response.headers.get('Content-Type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        console.error('Non-JSON response:', text);
        data = { error: 'Invalid server response format' };
      }
      
      if (!response.ok) {
        console.error('Error response:', data);
        return { error: data.error || `Failed to toggle user status (${response.status})` };
      }
      
      return { data };
    } catch (error) {
      console.error('Toggle status error:', error);
      return { error: 'Network error, please try again' };
    }
  },
  
  // Area Management API
  getAreas: async (): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/areas`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to fetch areas' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  addArea: async (areaData: AreaData): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/areas`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(areaData),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to add area' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Update Area
  updateArea: async (id: number, areaData: AreaData): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/areas/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(areaData),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to update area' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Delete Area
  deleteArea: async (id: number): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/areas/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to delete area' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // House Management API
  getHouses: async (): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/houses`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to fetch houses' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  addHouse: async (houseData: HouseData): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/houses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(houseData),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to add house' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Update House
  updateHouse: async (id: number, houseData: HouseData): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/houses/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(houseData),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to update house' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Delete House
  deleteHouse: async (id: number): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/houses/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to delete house' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Delete user (protected)
  deleteUser: async (userId: number): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        mode: 'cors'
      });
      
      // Handle non-JSON responses
      let data;
      const contentType = response.headers.get('Content-Type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        console.error('Non-JSON response:', text);
        data = { error: 'Invalid server response format' };
      }
      
      if (!response.ok) {
        console.error('Error response:', data);
        return { error: data.error || `Failed to delete user (${response.status})` };
      }
      
      return { data };
    } catch (error) {
      console.error('Delete user error:', error);
      return { error: 'Network error, please try again' };
    }
  },
  
  // Change password
  changePassword: async (passwordData: ChangePasswordData): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(passwordData),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to change password' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Bulk change status (activate/deactivate) for users across pages
  bulkChangeStatus: async (payload: BulkStatusChangePayload): Promise<ApiResponse<BulkOperationResult>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/users/bulk/status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to change users status' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Bulk delete users across pages
  bulkDeleteUsers: async (payload: BulkOperationPayload): Promise<ApiResponse<BulkOperationResult>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/users/bulk/delete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to delete users' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Bulk reset passwords for users across pages
  bulkResetPasswords: async (payload: BulkResetPasswordsPayload): Promise<ApiResponse<BulkOperationResult>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/users/bulk/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to reset user passwords' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },

  // Export users - allows downloading user data as Excel or CSV
  exportUsers: async (payload: ExportUsersPayload): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      // Default format is Excel if not specified
      const format = payload.format || 'excel';
      
      // Construct URL with query parameters for GET method
      let url = `${API_BASE_URL}/users/export?format=${format}&mode=${payload.mode}`;
      
      // Add userIds as query parameter if in 'selected' mode
      if (payload.mode === 'selected' && payload.userIds.length > 0) {
        url += `&userIds=${payload.userIds.join(',')}`;
      }
      
      // Add filter parameters if present
      if (payload.filters) {
        const { search, role, status, area, house } = payload.filters;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (role && role !== 'all') url += `&role=${encodeURIComponent(role)}`;
        if (status && status !== 'all') url += `&status=${encodeURIComponent(status)}`;
        if (area && area !== 'all') url += `&area=${encodeURIComponent(area)}`;
        if (house && house !== 'all') url += `&house=${encodeURIComponent(house)}`;
      }
      
      console.log("Export URL (GET method):", url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/octet-stream, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, text/csv'
        },
        mode: 'cors'
      });
      
      if (!response.ok) {
        // Sử dụng response.clone() để tạo một bản sao mà chúng ta có thể đọc
        try {
          const errorResponse = response.clone();
          const errorData = await errorResponse.json();
          return { error: errorData.error || errorData.message || `Server error: ${response.status}` };
        } catch (jsonError) {
          // Nếu không thể parse JSON, hãy thử đọc text từ bản sao khác
          try {
            const textResponse = response.clone();
            const errorText = await textResponse.text();
            console.error("Failed to parse server response as JSON:", errorText);
            return { error: `Server error ${response.status}: ${errorText.substring(0, 100)}...` };
          } catch (textError) {
            // Nếu cả hai cách đều thất bại, chỉ trả về mã lỗi HTTP
            return { error: `Server error: ${response.status}` };
          }
        }
      }
      
      // Handle the binary file response
      try {
        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'users-export';
        
        // Extract filename from Content-Disposition if available
        if (contentDisposition && contentDisposition.includes('filename=')) {
          const filenameMatch = contentDisposition.match(/filename="(.+)"/);
          if (filenameMatch && filenameMatch[1]) {
            filename = filenameMatch[1];
          } else {
            // Simple fallback if the regex doesn't match
            const parts = contentDisposition.split('filename=');
            if (parts.length > 1) {
              filename = parts[1].trim().replace(/"/g, '');
            }
          }
        } else {
          // Default filenames with timestamp
          const date = new Date().toISOString().split('T')[0];
          filename = format === 'csv' ? `users-export-${date}.csv` : `users-export-${date}.xlsx`;
        }
        
        // Create a download link and trigger it
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        return { data: { success: true, filename } };
      } catch (blobError) {
        console.error("Error processing file download:", blobError);
        const errorMessage = blobError instanceof Error ? blobError.message : 'Unknown error';
        return { error: `Error downloading file: ${errorMessage}` };
      }
    } catch (error: any) {
      console.error("Error exporting users:", error);
      return { error: `Network error: ${error.message || 'Failed to connect to server'}` };
    }
  },

  // Import users from Excel file (protected, admin only)
  importUsers: async (formData: FormData): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      console.log("API_BASE_URL:", API_BASE_URL);
      console.log("Calling import API endpoint:", `${API_BASE_URL}/users/import`);
      
      const response = await fetch(`${API_BASE_URL}/users/import`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
          // Note: Don't set Content-Type when sending FormData - browser will set it with boundary
        },
        body: formData
      });

      // First check if response is OK before parsing JSON
      if (!response.ok) {
        try {
          const errorData = await response.json();
          return { error: errorData.error || errorData.message || `Server error: ${response.status}` };
        } catch (jsonError) {
          // If can't parse JSON, get text
          const errorText = await response.text();
          console.error("Failed to parse server response as JSON:", errorText);
          return { error: `Server error ${response.status}: ${errorText.substring(0, 100)}...` };
        }
      }
      
      // Parse JSON response
      try {
        const data = await response.json();
        return { data, debug: { url: `${API_BASE_URL}/users/import`, status: response.status } };
      } catch (jsonError) {
        console.error("Error parsing successful response:", jsonError);
        return { error: 'Invalid response format from server' };
      }
    } catch (error: any) {
      console.error("Network error during user import:", error);
      return { error: `Network error: ${error.message || 'Failed to connect to server'}` };
    }
  },

  // Get all areas with their houses (protected)
  getAreasHouses: async (): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/areas-houses`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { error: data.error || 'Failed to fetch areas and houses' };
      }
      
      return { data };
    } catch (error) {
      return { error: 'Network error, please try again' };
    }
  },
  
  // Student Management API Endpoints
  
  // Get all students with optional filtering and pagination (protected)
  getStudents: async (pageOrFilters?: number | StudentFilters, perPage?: number, additionalFilters?: StudentFilters): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: "Authentication required" };
      }
      
      // Construct URL with pagination parameters
      let url = `${API_BASE_URL}/students`;
      
      // Add query params
      const queryParams: string[] = [];
      
      // Determine if first parameter is page number or filters object
      let actualFilters: StudentFilters | undefined;
      
      if (typeof pageOrFilters === "number") {
        // First param is page number
        // Add pagination params
        if (pageOrFilters !== undefined && perPage !== undefined) {
          queryParams.push(`page=${pageOrFilters}`);
          queryParams.push(`per_page=${perPage}`);
        }
        actualFilters = additionalFilters;
      } else {
        // First param is filters object
        actualFilters = pageOrFilters;
      }
      
      // Add filter params if they exist
      if (actualFilters) {
        if (actualFilters.search) {
          queryParams.push(`search=${encodeURIComponent(actualFilters.search)}`);
        }
        
        if (actualFilters.status && actualFilters.status !== "all") {
          queryParams.push(`status=${encodeURIComponent(actualFilters.status)}`);
        }
          
        if (actualFilters.matched && actualFilters.matched !== "all") {
          queryParams.push(`matched=${encodeURIComponent(actualFilters.matched)}`);
        }
        
        if (actualFilters.area && actualFilters.area !== "all") {
          queryParams.push(`area=${encodeURIComponent(actualFilters.area)}`);
        }
          
        if (actualFilters.house && actualFilters.house !== "all") {
          queryParams.push(`house=${encodeURIComponent(actualFilters.house)}`);
        }
      }
      
      // Append query string if we have params
      if (queryParams.length > 0) {
        url = `${url}?${queryParams.join("&")}`;
      }
      
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10-second timeout
        
        const response = await fetch(url, {
          headers: {
            "Authorization": `Bearer ${token}`,
            "Accept": "application/json"
          },
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        // Check if the response is valid JSON
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const data = await response.json();
          
          if (!response.ok) {
            return { error: data.error || "Failed to fetch students" };
          }
          
          return { data };
        } else {
          // Handle non-JSON response
          const text = await response.text();
          console.error("Non-JSON response:", text);
          return { error: `Received non-JSON response: ${text.substring(0, 100)}...` };
        }
      } catch (fetchError: any) {
        if (fetchError.name === "AbortError") {
          return { error: "Request timed out" };
        }
        throw fetchError;
      }
    } catch (error: any) {
      console.error("Error fetching students:", error);
      return { error: `Network error: ${error.message || "Failed to connect to server"}` };
    }
  },
  
  // Create a new student (protected)
  createStudent: async (studentData: any): Promise<ApiResponse<any>> => {
    try {
      const token = getToken();
      if (!token) {
        return { error: 'Authentication required' };
      }
      
      const response = await fetch(`${API_BASE_URL}/students`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(studentData)
      });
      
      if (!response.ok) {
        try {
          const errorData = await response.json();
          return { error: errorData.error || errorData.message || `Server error: ${response.status}` };
        } catch (jsonError) {
          const errorText = await response.text();
          return { error: `Server error ${response.status}: ${errorText.substring(0, 100)}...` };
        }
      }
      
      const data = await response.json();
      return { data };
    } catch (error: any) {
      return { error: `Network error: ${error.message || 'Failed to connect to server'}` };
    }
  },
}
  
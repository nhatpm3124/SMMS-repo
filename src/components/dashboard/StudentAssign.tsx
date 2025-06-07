const fetchStudents = async (
  pageToFetch: number = studentPage,
  checkAllPages: boolean = false
): Promise<void> => {
  setStudentLoading(true);
  try {
    // ... existing code logic ...
  } catch (error) {
    // ... error handling ...
  } finally {
    setStudentLoading(false);
  }
}; 
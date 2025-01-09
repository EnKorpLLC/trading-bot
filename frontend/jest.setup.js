// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Mock next/router
jest.mock('next/router', () => require('next-router-mock'));

// Mock next/navigation
const useRouter = jest.fn();
const usePathname = jest.fn();
const useSearchParams = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter,
  usePathname,
  useSearchParams,
}));

// Reset all mocks before each test
beforeEach(() => {
  useRouter.mockReset();
  usePathname.mockReset();
  useSearchParams.mockReset();
}); 
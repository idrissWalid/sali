"use client";

import { useEffect, ReactNode } from "react";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogCancel
} from "./AlertDialog";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  maxWidth?: string;
}

export default function Modal({ isOpen, onClose, title, children, maxWidth = "500px" }: ModalProps) {
  return (
    <AlertDialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <AlertDialogContent style={{ maxWidth }} className="sm:max-w-none">
        <AlertDialogCancel 
          onClick={onClose}
          className="absolute right-6 top-6 rounded-sm opacity-70 transition-opacity hover:opacity-100 outline-none hover:bg-transparent border-none p-0 m-0"
          style={{ color: "var(--text-muted)", border: "none", background: "transparent", minWidth: "auto", height: "auto" }}
        >
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M11.7816 4.03157C12.0062 3.80702 12.0062 3.44295 11.7816 3.2184C11.5571 2.99385 11.193 2.99385 10.9685 3.2184L7.50005 6.68682L4.03164 3.2184C3.80708 2.99385 3.44301 2.99385 3.21846 3.2184C2.99391 3.44295 2.99391 3.80702 3.21846 4.03157L6.68688 7.49999L3.21846 10.9684C2.99391 11.193 2.99391 11.557 3.21846 11.7816C3.44301 12.0061 3.80708 12.0061 4.03164 11.7816L7.50005 8.31316L10.9685 11.7816C11.193 12.0061 11.5571 12.0061 11.7816 11.7816C12.0062 11.557 12.0062 11.193 11.7816 10.9684L8.31322 7.49999L11.7816 4.03157Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
          </svg>
        </AlertDialogCancel>

        <AlertDialogHeader className="flex flex-col space-y-1.5 text-left mb-2">
          <AlertDialogTitle className="text-xl font-semibold leading-none tracking-tight" style={{ paddingRight: "24px" }}>
            {title}
          </AlertDialogTitle>
        </AlertDialogHeader>
        <AlertDialogDescription className="hidden">Modal dialog</AlertDialogDescription>
        <div style={{ color: "var(--text-main)", overflowY: "auto", maxHeight: "70vh", fontSize: "14px", lineHeight: 1.6 }}>
          {children}
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}

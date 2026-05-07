import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { FileUp, MousePointerClick } from "lucide-react";

interface Props {
  onFiles: (files: File[]) => void;
  multiple?: boolean;
  accept?: string;
  label?: string;
}

export default function FileDropzone({
  onFiles,
  multiple = false,
  accept = ".pdf",
  label = "Drop PDF files here, or click to browse",
}: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length) onFiles(accepted);
    },
    [onFiles]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple,
    accept: { "application/pdf": accept.split(",").map((item) => item.trim()) },
  });

  return (
    <div
      {...getRootProps()}
      className={`dropzone ${isDragActive ? "dropzone-active" : ""}`}
    >
      <input {...getInputProps()} />
      <div className="dropzone-content">
        <div className="dropzone-cube">
          <FileUp size={38} />
          <MousePointerClick size={17} className="dropzone-pointer" />
        </div>
        <p>{isDragActive ? "Drop the files here..." : label}</p>
      </div>
    </div>
  );
}
